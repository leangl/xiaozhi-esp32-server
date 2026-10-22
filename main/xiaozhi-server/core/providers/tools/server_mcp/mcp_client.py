"""Server-side MCP client."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import copy
import concurrent.futures
from contextlib import AsyncExitStack
from typing import Optional, List, Dict, Any

from mcp import ClientSession, Implementation
from mcp.client.session import SamplingFnT, ElicitationFnT, ListRootsFnT, LoggingFnT, MessageHandlerFnT
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.session import ProgressFnT

from config.logger import setup_logging
from config.service_policy import ServicePolicyError, validate_endpoint, mcp_httpx_client
from core.utils.util import sanitize_tool_name

TAG = __name__


class ServerMCPClient:
    """Connect to and manage server-side MCP services."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the server-side MCP client

        Args:
            config: MCP service configuration dictionary.
        """
        self.logger = setup_logging()
        # No process/package installers in the supported backend. Operate tool
        # servers independently and expose a reviewed HTTP/SSE endpoint.
        if "command" in config or "args" in config or "env" in config:
            raise ServicePolicyError("MCP subprocess transport is unavailable; configure a reviewed HTTP service")
        validate_endpoint(config.get("url"), "mcp")
        if config.get("transport", "sse") not in {"sse", "streamable-http", "http"}:
            raise ServicePolicyError("MCP transport is unavailable")
        self.config = copy.deepcopy(config)

        self._worker_task: Optional[asyncio.Task] = None
        self._ready_evt = asyncio.Event()
        self._shutdown_evt = asyncio.Event()

        self.session: Optional[ClientSession] = None
        self.tools: List = []  # Original tool objects
        self.tools_dict: Dict[str, Any] = {}
        self.name_mapping: Dict[str, str] = {}

    async def initialize(self, read_timeout_seconds: timedelta | None = None,
             sampling_callback: SamplingFnT | None = None,
             elicitation_callback: ElicitationFnT | None = None,
             list_roots_callback: ListRootsFnT | None = None,
             logging_callback: LoggingFnT | None = None,
             message_handler: MessageHandlerFnT | None = None,
             client_info: Implementation | None = None):
        """Initialize the MCP client connection."""
        if self._worker_task:
            return

        self._worker_task = asyncio.create_task(
            self._worker(read_timeout_seconds=read_timeout_seconds,
                        sampling_callback=sampling_callback,
                        elicitation_callback=elicitation_callback,
                        list_roots_callback=list_roots_callback,
                        logging_callback=logging_callback,
                        message_handler=message_handler,
                        client_info=client_info), name="ServerMCPClientWorker"
        )
        await self._ready_evt.wait()
        if self._worker_task.done():
            await self._worker_task

        self.logger.bind(tag=TAG).info(
            f"Server-side MCP client connected; available tools: {[name for name in self.name_mapping.values()]}"
        )

    async def cleanup(self):
        """Clean up MCP client resources."""
        if not self._worker_task:
            return

        self._shutdown_evt.set()
        try:
            await asyncio.wait_for(self._worker_task, timeout=20)
        except (asyncio.TimeoutError, Exception) as e:
            self.logger.bind(tag=TAG).error("Error closing server-side MCP client")
        finally:
            self._worker_task = None

    def has_tool(self, name: str) -> bool:
        """Check whether the specified tool exists.

        Args:
            name: Tool name.

        Returns:
            bool: Whether the tool exists.
        """
        return name in self.tools_dict

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get definitions for all available tools.

        Returns:
            List[Dict[str, Any]]: Tool definitions.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for name, tool in self.tools_dict.items()
        ]

    async def call_tool(self, name: str, arguments: dict, read_timeout_seconds: timedelta | None = None, progress_callback: ProgressFnT | None = None, *, meta: dict[str, Any] | None = None) -> Any:
        """Call the specified tool.

        Args:
            name: Tool name.
            arguments: Tool arguments.
            read_timeout_seconds:
            progress_callback: Progress callback.
            meta:

        Returns:
            Any: Tool execution result.

        Raises:
            RuntimeError: Raised when the client has not been initialized.
        """
        if not self.session:
            raise RuntimeError("服务端MCP客户端未初始化")

        real_name = self.name_mapping.get(name, name)
        loop = self._worker_task.get_loop()
        coro = self.session.call_tool(real_name, arguments=arguments, read_timeout_seconds=read_timeout_seconds, progress_callback=progress_callback, meta=meta)

        if loop is asyncio.get_running_loop():
            return await coro

        fut: concurrent.futures.Future = asyncio.run_coroutine_threadsafe(coro, loop)
        return await asyncio.wrap_future(fut)

    def is_connected(self) -> bool:
        """Check whether the MCP client is connected and healthy.

        Returns:
            bool: True if the client is connected and working, otherwise False.
        """
        # Check whether the worker task exists
        if self._worker_task is None:
            return False

        # Check whether the worker task has completed or been canceled
        if self._worker_task.done():
            return False

        # Check whether the session exists
        if self.session is None:
            return False

        # All checks passed; the connection is healthy
        return True

    async def _worker(self, read_timeout_seconds: timedelta | None = None,
             sampling_callback: SamplingFnT | None = None,
             elicitation_callback: ElicitationFnT | None = None,
             list_roots_callback: ListRootsFnT | None = None,
             logging_callback: LoggingFnT | None = None,
             message_handler: MessageHandlerFnT | None = None,
             client_info: Implementation | None = None):
        """MCP client worker coroutine."""
        async with AsyncExitStack() as stack:
            try:
                validate_endpoint(self.config.get("url"), "mcp")
                if "url" in self.config:
                    headers = dict(self.config.get("headers", {}))
                    # TODO: support legacy versions
                    if "API_ACCESS_TOKEN" in self.config:
                        headers["Authorization"] = f"Bearer {self.config['API_ACCESS_TOKEN']}"
                        self.logger.bind(tag=TAG).warning(f"You are using the deprecated API_ACCESS_TOKEN setting. In .mcp_server_settings.json, set API_ACCESS_TOKEN directly in headers, for example 'Authorization': 'Bearer API_ACCESS_TOKEN'")
                   
                    # Choose the client by transport type; default to SSE
                    transport_type = self.config.get("transport", "sse")

                    if transport_type == "streamable-http" or transport_type == "http":
                        # Use Streamable HTTP transport
                        http_r, http_w, get_session_id = await stack.enter_async_context(
                            streamablehttp_client(
                                url=self.config["url"],
                                headers=headers,
                                timeout=self.config.get("timeout", 30),
                                sse_read_timeout=self.config.get("sse_read_timeout", 60 * 5),
                                terminate_on_close=self.config.get("terminate_on_close", True),
                                httpx_client_factory=mcp_httpx_client
                            )
                        )
                        read_stream, write_stream = http_r, http_w
                    else:
                        # Use traditional SSE transport
                        sse_r, sse_w = await stack.enter_async_context(
                            sse_client(
                                url=self.config["url"],
                                headers=headers,
                                timeout=self.config.get("timeout", 5),
                                sse_read_timeout=self.config.get("sse_read_timeout", 60 * 5),
                                httpx_client_factory=mcp_httpx_client
                            )
                        )
                        read_stream, write_stream = sse_r, sse_w

                else:
                    raise ServicePolicyError("MCP configuration requires a reviewed HTTP endpoint")

                self.session = await stack.enter_async_context(
                    ClientSession(
                        read_stream=read_stream,
                        write_stream=write_stream,
                        read_timeout_seconds=read_timeout_seconds,
                        sampling_callback=sampling_callback,
                        elicitation_callback=elicitation_callback,
                        list_roots_callback=list_roots_callback,
                        logging_callback=logging_callback,
                        message_handler=message_handler,
                        client_info=client_info
                    )
                )
                await self.session.initialize()

                # Get tools
                self.tools = (await self.session.list_tools()).tools
                for t in self.tools:
                    sanitized = sanitize_tool_name(t.name)
                    self.tools_dict[sanitized] = t
                    self.name_mapping[sanitized] = t.name

                self._ready_evt.set()

                # Suspend until closure
                await self._shutdown_evt.wait()

            except Exception:
                self.logger.bind(tag=TAG).error("Server-side MCP connection unavailable")
                self._ready_evt.set()
                raise
