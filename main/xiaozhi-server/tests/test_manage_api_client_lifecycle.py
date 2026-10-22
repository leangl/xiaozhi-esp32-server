"""ManageApiClient lifecycle regression tests: run with unittest, without the app, models or network.

Excluded from pytest: tests/conftest.py globally mocks asyncio.sleep and
httpx.AsyncClient at import time, interfering with the timing assertions and
MockTransport injection here. __test__ = False disables pytest collection;
run these tests directly with unittest.
Usage: python -B tests/test_manage_api_client_lifecycle.py -v
"""
__test__ = False

import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import weakref

import httpx


class ManageApiClientLifecycleTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        source = Path(os.environ.get('CLIENT_UNDER_TEST', str(
            Path(__file__).resolve().parents[1] / 'config/manage_api_client.py')))
        spec = importlib.util.spec_from_file_location('_lifecycle_client', source)
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)
        self.cls = self.api.ManageApiClient
        self.cls({'manager-api': {'url': 'http://127.0.0.1:9100/xiaozhi',
                  'secret': 'synthetic-test', 'max_retries': 1, 'retry_delay': 0}})
        self.clients = []
        self.requests = []
        self.real_client = httpx.AsyncClient

    def transport(self, handler):
        def factory(**kwargs):
            async def handle(request):
                self.requests.append(request)
                return await handler(request)
            client = self.real_client(transport=httpx.MockTransport(handle), **kwargs)
            self.clients.append(client)
            return client
        return patch.object(self.api.httpx, 'AsyncClient', side_effect=factory)

    async def asyncTearDown(self):
        try:
            self.assertTrue(all(c.is_closed for c in self.clients), 'client escaped its request')
        finally:
            for client in self.clients:
                if not client.is_closed:
                    await client.aclose()
            self.cls.safe_close()

    async def test_success_preserves_url_headers_and_payload(self):
        async def handle(request):
            self.assertEqual(str(request.url), 'http://127.0.0.1:9100/xiaozhi/report')
            self.assertEqual(request.headers['authorization'], 'Bearer synthetic-test')
            self.assertEqual(request.content, b'{"value":123}')
            return httpx.Response(200, json={'code': 0, 'data': {'ok': True}})
        with self.transport(handle):
            self.assertEqual(await self.cls._execute_async_request('POST', '/report',
                             json={'value': 123}), {'ok': True})

    async def test_retry_reuses_client_until_request_ends(self):
        """Retries reuse one client (and the same pooled keep-alive connection).
        Close it only when the whole application request ends: client lifetime
        follows the request, not an individual attempt."""
        async def handle(request):
            if len(self.requests) == 1:
                return httpx.Response(503)
            # The first client is still active during the second attempt, not closed early.
            self.assertFalse(self.clients[0].is_closed)
            return httpx.Response(200, json={'code': 0, 'data': True})
        with self.transport(handle):
            self.assertTrue(await self.cls._execute_async_request('POST', '/report'))
        self.assertEqual(len(self.clients), 1)
        self.assertTrue(self.clients[0].is_closed)

    async def test_timeout_exhaustion_reuses_client_until_request_ends(self):
        async def handle(request):
            raise httpx.ReadTimeout('synthetic timeout', request=request)
        with self.transport(handle), self.assertRaises(httpx.ReadTimeout):
            await self.cls._execute_async_request('POST', '/report')
        self.assertEqual(len(self.clients), 1)
        self.assertTrue(self.clients[0].is_closed)

    async def test_remote_protocol_error_without_response_triggers_retry(self):
        """Stale keep-alive: no response has started, so retrying is safe."""
        async def handle(request):
            if len(self.requests) == 1:
                raise httpx.RemoteProtocolError(
                    'Server disconnected without sending a response.',
                    request=request)
            return httpx.Response(200, json={'code': 0, 'data': True})
        with self.transport(handle):
            self.assertTrue(await self.cls._execute_async_request('POST', '/report'))
        self.assertEqual(len(self.requests), 2)

    async def test_remote_protocol_error_incomplete_body_not_retried(self):
        """A truncated response likely follows a processed request. Retrying a
        non-idempotent POST could duplicate it; fail immediately instead."""
        async def handle(request):
            raise httpx.RemoteProtocolError(
                'Peer closed connection without sending complete message body '
                '(discarded 10 of 100 read bytes)', request=request)
        with self.transport(handle), self.assertRaises(httpx.RemoteProtocolError):
            await self.cls._execute_async_request('POST', '/report')
        self.assertEqual(len(self.requests), 1)

    async def test_nonretryable_http_error(self):
        async def handle(request):
            return httpx.Response(403)
        with self.transport(handle), self.assertRaises(httpx.HTTPStatusError):
            await self.cls._execute_async_request('POST', '/report')
        self.assertEqual(len(self.clients), 1)

    async def test_business_error_and_invalid_json_release_client(self):
        for response, error in [
            (httpx.Response(200, json={'code': 10041, 'msg': 'missing'}), self.api.DeviceNotFoundException),
            (httpx.Response(200, json={'code': 10042, 'msg': 'bind'}), self.api.DeviceBindException),
            (httpx.Response(200, content=b'not-json'), ValueError),
        ]:
            async def handle(request):
                return response
            with self.transport(handle), self.assertRaises(error):
                await self.cls._execute_async_request('POST', '/report')
            self.assertTrue(self.clients[-1].is_closed)
        self.assertEqual(len(self.clients), 3)

    async def test_cancellation_does_not_close_concurrent_request(self):
        entered = [asyncio.Event(), asyncio.Event()]
        release = asyncio.Event()
        async def handle(request):
            index = len(self.requests) - 1
            entered[index].set()
            await release.wait()
            return httpx.Response(200, json={'code': 0, 'data': True})
        with self.transport(handle):
            first = asyncio.create_task(self.cls._execute_async_request('POST', '/first'))
            await asyncio.wait_for(entered[0].wait(), 2)
            second = asyncio.create_task(self.cls._execute_async_request('POST', '/second'))
            await asyncio.wait_for(entered[1].wait(), 2)
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            self.assertTrue(self.clients[0].is_closed)
            self.assertFalse(self.clients[1].is_closed)
            release.set()
            self.assertTrue(await asyncio.wait_for(second, 2))

    async def test_shutdown_allows_inflight_cleanup_and_blocks_report_entry(self):
        async def handle(request):
            self.cls.safe_close()
            return httpx.Response(200, json={'code': 0, 'data': True})
        with self.transport(handle):
            self.assertTrue(await self.api.report('device', 'session', 1, 'text', None, 0))
            self.assertIsNone(await self.api.report('device', 'session', 1, 'later', None, 0))
            # Compatibility fixture: existing consumers match this Chinese error fragment.
            with self.assertRaisesRegex(Exception, '已关闭'):
                await self.cls._execute_async_request('POST', '/report')
        self.assertEqual(len(self.clients), 1)

    async def test_safe_close_interrupts_retry_backoff(self):
        """safe_close interrupts retry waits: let the active attempt finish and
        start no new attempts. Raise ManageApiShutdownError, distinguishable from
        a network error after exhausted retries."""
        async def handle(request):
            return httpx.Response(503)
        original_delay = self.cls.retry_delay
        self.cls.retry_delay = 5.0  # setUp uses zero, which cannot expose an interrupted wait.
        try:
            with self.transport(handle):
                task = asyncio.create_task(
                    self.cls._execute_async_request('POST', '/report'))
                await asyncio.sleep(0.2)  # Allow the request to enter its retry wait.
                self.cls.safe_close()
                with self.assertRaises(self.api.ManageApiShutdownError) as ctx:
                    await task
                self.assertIsInstance(ctx.exception.__cause__, httpx.HTTPStatusError)
            # Only the first attempt ran: the wait was interrupted before another attempt.
            self.assertEqual(len(self.clients), 1)
            self.assertEqual(len(self.requests), 1)
        finally:
            self.cls.retry_delay = original_delay

    async def test_many_temporary_loops_leave_no_open_clients(self):
        async def handle(request):
            return httpx.Response(200, json={'code': 0, 'data': True})
        def report_once(_):
            return asyncio.run(self.cls._execute_async_request('POST', '/report'))
        with self.transport(handle), ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(report_once, range(100)))
        self.assertTrue(all(results))
        self.assertEqual(len(self.clients), 100)
        self.assertTrue(all(c.is_closed for c in self.clients))
        # Cache regression guard: clients must be collectible once test references are released.
        # Reintroducing class-level caches (id(loop) dict / WeakKeyDictionary) leaves survivors.
        refs = [weakref.ref(c) for c in self.clients]
        self.clients.clear()
        gc.collect()
        self.assertEqual(sum(ref() is not None for ref in refs), 0)


if __name__ == '__main__':
    unittest.main()
