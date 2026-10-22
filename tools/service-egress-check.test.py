#!/usr/bin/env python3
r"""Parser tests everywhere; live strace tests ONLY in Linux --network none.

    python -B tools/service-egress-check.test.py
    docker run --rm --init --network none --read-only --cap-drop ALL \
      --tmpfs /tmp:rw,nosuid,nodev,size=1g --pids-limit 512 \
      xiaozhi-policy/egress-observer:20261021 \
      python -B /opt/egress-observer/service-egress-check.test.py

The observer image sets EGRESS_REQUIRE_STRACE=1: live tests cannot silently
skip due to absent strace or a non-isolated namespace. If tracing is denied,
retry with --cap-add SYS_PTRACE only; no privileged/unconfined runner.
No network namespace with an external interface is permitted for live tests.
No trace lines, child payloads, argv or raw errors are printed on failures.
"""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


spec = importlib.util.spec_from_file_location("egress_check", Path(__file__).with_name("service-egress-check.py"))
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
SECRET = "synthetic-DO-NOT-RECORD-credentials-audio-18fe32b7"


def inet(ip="127.0.0.1", port=18080):
    return f'{{sa_family=AF_INET, sin_port=htons({port}), sin_addr=inet_addr("{ip}")}}'


def inet6(ip="::1", port=18080):
    return (f'{{sa_family=AF_INET6, sin6_port=htons({port}), sin6_flowinfo=htonl(0), '
            f'inet_pton(AF_INET6, "{ip}", &sin6_addr), sin6_scope_id=0}}')


def mmsg(*names):
    return '[' + ', '.join(
        '{msg_hdr={msg_name=' + name + ', msg_namelen=16, '
        'msg_iov=[{iov_base=""..., iov_len=4}], msg_iovlen=1}, msg_len=4}'
        for name in names) + ']'


class CandidateParserTests(unittest.TestCase):
    def policy(self, **kwargs):
        return observer.Policy(endpoints=(("127.0.0.1", 18080), ("172.30.7.2", 3306),
                                          ("172.30.7.3", 6379)), candidate=True, **kwargs)

    def test_candidate_mode_is_explicit_and_exact(self):
        with self.assertRaises(ValueError):
            observer.Policy(endpoints=(("172.30.7.2", 3306),))
        policy = self.policy()
        result = observer.parse_trace([
            f'1 connect(4, {inet("172.30.7.2", 3306)}, 16) = 0',
            f'2 connect(4, {inet("172.30.7.2", 443)}, 16) = -1 ECONNREFUSED (refused)',
            f'3 connect(4, {inet("172.30.7.9", 3306)}, 16) = -1 ENETUNREACH (unreachable)',
        ], policy)
        self.assertEqual((result["attempt_count"], result["denied_count"], result["parse_errors"]), (3, 2, {}))
        self.assertEqual(policy.summary()["mode"], "exact_candidate_endpoints")
        with self.assertRaises(ValueError):
            observer.Policy(candidate=True, broad=True)

    def test_mapped_ipv4_has_same_exact_policy_as_ipv4(self):
        policy = self.policy()
        result = observer.parse_trace([
            f'1 connect(4, {inet6("::ffff:172.30.7.2", 3306)}, 28) = 0',
            f'1 connect(5, {inet6("::ffff:172.30.7.2", 3307)}, 28) = 0',
            f'1 connect(6, {inet6("::ffff:198.51.100.1", 443)}, 28) = 0',
        ], policy)
        self.assertEqual((result["denied_count"], result["parse_errors"]), (2, {}))
        self.assertEqual(result["attempts"][0]["ip"], "172.30.7.2")
        self.assertEqual(result["attempts"][0]["family"], "AF_INET6")

    def test_default_and_broad_mapped_loopback_do_not_allow_remote(self):
        for policy in (observer.Policy(endpoints=(("127.0.0.1", 18080),)), observer.Policy(broad=True)):
            result = observer.parse_trace([
                f'1 connect(4, {inet6("::ffff:127.0.0.1")}, 28) = 0',
                f'1 connect(5, {inet6("::ffff:127.0.0.2")}, 28) = 0',
                f'1 connect(6, {inet6("::ffff:198.51.100.1")}, 28) = 0',
            ], policy)
            self.assertEqual(result["denied_count"], 2)

    def test_reply_allowance_requires_exact_local_direction_and_peer_ip(self):
        policy = self.policy(local_endpoints=(("127.0.0.1", 18080),), reply_peer_ips=("127.0.0.1",))
        pairs = ["127.0.0.1:18080->127.0.0.1:31000",  # accepted reply
                 "127.0.0.1:18081->127.0.0.1:31000",  # wrong local port
                 "127.0.0.1:18080->198.51.100.2:31000",  # untrusted peer
                 "127.0.0.2:18080->127.0.0.1:31000",  # wrong local IP
                 "127.0.0.1:31000->127.0.0.1:18081"]  # reversed direction
        result = observer.parse_trace([
            f'1 sendto(3<TCP:[{pair}]>, ""..., 4, 0, NULL, 0) = 4' for pair in pairs
        ], policy)
        self.assertEqual((result["denied_count"], result["parse_errors"]), (4, {}))
        self.assertEqual(result["attempts"][0]["policy_basis"], "accepted_reply")
        self.assertEqual(result["attempts"][0]["local_port"], 18080)
        for bad in ({"local_endpoints": (("127.0.0.1", 18080),)}, {"reply_peer_ips": ("127.0.0.1",)}):
            with self.assertRaises(ValueError):
                observer.Policy(**bad)

    def test_reply_allowance_never_applies_to_connect_explicit_destination_or_udp(self):
        policy = self.policy(local_endpoints=(("127.0.0.1", 18080),), reply_peer_ips=("127.0.0.1",))
        fd = '3<TCP:[127.0.0.1:18080->127.0.0.1:31000]>'
        result = observer.parse_trace([
            f'1 connect({fd}, {inet(port=31000)}, 16) = 0',
            f'1 sendto({fd}, ""..., 4, 0, {inet(port=31000)}, 16) = 4',
            '1 sendmsg(3<UDP:[127.0.0.1:18080->127.0.0.1:31000]>, {msg_name=NULL}, 0) = 4',
            '1 sendto(3<TCP:[127.0.0.1:18080]>, ""..., 4, 0, NULL, 0) = 4',
        ], policy)
        self.assertEqual(result["denied_count"], 4)

    def test_ipv6_and_mapped_accepted_replies(self):
        policy = self.policy(local_endpoints=(("::1", 18080), ("127.0.0.1", 18080)),
                             reply_peer_ips=("::1", "127.0.0.1"))
        result = observer.parse_trace([
            '1 sendmsg(3<TCPv6:[[::1]:18080->[::1]:41000]>, {msg_name=NULL}, 0) = 4',
            '1 sendmsg(3<TCPv6:[[::ffff:127.0.0.1]:18080->[::ffff:127.0.0.1]:41000]>, {msg_name=NULL}, 0) = 4',
        ], policy)
        self.assertEqual((result["denied_count"], result["parse_errors"]), (0, {}))

    def test_sendmmsg_checks_every_name_even_when_batch_fails_or_partially_sends(self):
        for returned in ('-1 ENETUNREACH (unreachable)', '1', '2'):
            result = observer.parse_trace([
                f'1 sendmmsg(3, {mmsg(inet(), inet("198.51.100.1", 53))}, 2, 0) = {returned}',
            ], self.policy())
            self.assertEqual((result["attempt_count"], result["denied_count"], result["parse_errors"]), (2, 1, {}))

    def test_sendmmsg_connected_names_and_unresolved_names(self):
        for fd, denied in [('3<TCP:[127.0.0.1:31000->127.0.0.1:18080]>', 0), ('3', 2)]:
            result = observer.parse_trace([f'1 sendmmsg({fd}, {mmsg("NULL", "NULL")}, 2, 0) = 2'], self.policy())
            self.assertEqual(result["denied_count"], denied)
        for vector, count in [('0x1234', 2), ('[' + mmsg(inet())[1:-1] + ', ...]', 2), (mmsg(inet()), 2)]:
            result = observer.parse_trace([f'1 sendmmsg(3, {vector}, {count}, 0) = -1 EFAULT (bad)'], self.policy())
            self.assertTrue(result["parse_errors"], "opaque/truncated/missing destinations must fail closed")

    def test_netlink_is_only_allowed_to_kernel_without_multicast(self):
        for pid, groups, allowed in [('0', '00000000', True), ('0', '0x0', True),
                                      ('9', '0', False), ('0', '0x1', False), ('0', '1', False)]:
            addr = f'{{sa_family=AF_NETLINK, nl_pid={pid}, nl_groups={groups}}}'
            result = observer.parse_trace([f'1 sendmsg(3, {{msg_name={addr}}}, 0) = 4'], self.policy())
            self.assertEqual(result["denied_count"], 0 if allowed else 1)

    def test_unspec_only_allows_explicit_connect_disconnect(self):
        result = observer.parse_trace([
            '1 connect(3, {sa_family=AF_UNSPEC, sa_data=""...}, 16) = 0',
            '1 sendto(3, ""..., 4, 0, {sa_family=AF_UNSPEC}, 16) = 4',
        ], self.policy())
        self.assertEqual(result["denied_count"], 1)
        self.assertTrue(result["attempts"][0]["allowed"])

    def test_io_uring_submit_paths_are_fail_closed_even_when_blocked(self):
        for name in ('io_uring_enter', 'io_uring_register'):
            result = observer.parse_trace([f'1 {name}(4, 0x1234, 0) = -1 EPERM (blocked)'], self.policy())
            self.assertEqual(result["denied_count"], 1)
            self.assertIn("unsupported_unobserved_network_path", result["parse_errors"])

    def test_only_refused_setup_probes_cannot_create_unobserved_io(self):
        for error in ("EPERM", "EACCES", "ENOSYS"):
            result = observer.parse_trace([f'1 io_uring_setup(256, {{flags=0}}) = -1 {error} (blocked)'], self.policy())
            self.assertEqual((result["denied_count"], result["parse_errors"]), (0, {}))
            self.assertEqual(result["attempts"][0]["policy_basis"], "kernel_refused_io_uring_setup")
        for returned in ("3", "0", "-1 EINVAL (ambiguous)"):
            result = observer.parse_trace([f'1 io_uring_setup(256, {{flags=0}}) = {returned}'], self.policy())
            self.assertEqual(result["denied_count"], 1)
            self.assertIn("unsupported_unobserved_network_path", result["parse_errors"])

    def test_clone_thread_and_batch_unfinished_resumed_interleaving(self):
        result = observer.parse_trace([
            '1 clone3({flags=CLONE_VM|CLONE_THREAD, exit_signal=0}, 88 <unfinished ...>',
            '2 sendmmsg(3, ' + mmsg(inet(), inet("172.30.7.3", 6379)) + ', 2, 0 <unfinished ...>',
            '1 <... clone3 resumed>) = 2',
            '3 clone(child_stack=NULL, flags=CLONE_VM|CLONE_THREAD) = -1 ENOSYS (not implemented)',
            '2 <... sendmmsg resumed>) = 2',
        ], self.policy())
        self.assertEqual((result["attempt_count"], result["denied_count"], result["parse_errors"]), (2, 0, {}))

    def test_epoch_metadata_with_and_without_pid_prefix(self):
        result = observer.parse_trace([
            f'100 1792551000.123456 connect(3, {inet()}, 16) = 0',
            f'[pid 101] 1792551001.654321 connect(3, {inet()}, 16) = 0',
            f'1792551002.000001 connect(3, {inet()}, 16) = 0',
            f'102 connect(3, {inet()}, 16) = 0',
        ], self.policy())
        self.assertEqual(result["parse_errors"], {})
        events = result["attempts"]
        self.assertEqual([e["pid"] for e in events], [100, 101, 0, 102])
        self.assertEqual([e["timestamp"] for e in events[:3]],
                         [1792551000.123456, 1792551001.654321, 1792551002.000001])
        self.assertNotIn("timestamp", events[3])

    def test_epoch_unfinished_uses_start_not_resume_and_does_not_merge_phases(self):
        result = observer.parse_trace([
            f'100 1792551000.100000 connect(3, {inet()}, 16 <unfinished ...>',
            f'101 1792551000.200000 sendmmsg(4, {mmsg(inet(), inet("172.30.7.3", 6379))}, 2, 0 <unfinished ...>',
            '100 1792551009.100000 <... connect resumed>) = 0',
            '101 1792551010.100000 <... sendmmsg resumed>) = 2',
            f'100 1792551011.100000 connect(3, {inet()}, 16) = 0',
        ], self.policy())
        self.assertEqual((result["attempt_count"], result["parse_errors"]), (4, {}))
        self.assertEqual([e["timestamp"] for e in result["attempts"]],
                         [1792551000.1, 1792551000.2, 1792551000.2, 1792551011.1])

    def test_epoch_missing_start_timestamp_not_replaced_by_resume(self):
        result = observer.parse_trace([
            f'100 connect(3, {inet()}, 16 <unfinished ...>',
            '100 1792551009.100000 <... connect resumed>) = 0',
        ], self.policy())
        self.assertNotIn("timestamp", result["attempts"][0])
        self.assertEqual(result["parse_errors"], {})

    def test_pending_call_at_eof_retains_start_timestamp(self):
        result = observer.parse_trace([
            f'100 1792551000.123456 connect(3, {inet("198.51.100.1", 443)}, 16 <unfinished ...>',
        ], self.policy())
        self.assertEqual(result["attempts"][0]["timestamp"], 1792551000.123456)
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("incomplete_syscall", result["parse_errors"])

    def test_exact_dns53_only_at_reviewed_fixture_address(self):
        policy = observer.Policy(endpoints=(("127.0.0.1", 53),), candidate=True)
        result = observer.parse_trace([
            f'1 sendmmsg(3, {mmsg(inet("127.0.0.1", 53), inet("127.0.0.53", 53))}, 2, 0) = 2',
        ], policy)
        self.assertEqual((result["denied_count"], result["parse_errors"]), (1, {}))

    def test_raw_payload_and_unix_paths_redacted_in_full_report(self):
        policy = self.policy()
        vector = mmsg(inet(), '{sa_family=AF_UNIX, sun_path="' + SECRET + '"}')
        vector = vector.replace('iov_base=""...', 'iov_base="' + SECRET + ', sa_family=AF_INET"')
        parsed = observer.parse_trace([f'1 sendmmsg(3, {vector}, 2, 0) = 2'], policy)
        report = observer.make_report(parsed, policy, 0)
        self.assertEqual(report["result"], "pass")
        self.assertTrue(SECRET not in json.dumps(report), "report must not contain trace payload/path")

    def test_only_numeric_exact_candidate_addresses_and_no_wildcard_reply(self):
        for ip in ("candidate-db", "172.30.7.0/24", "0.0.0.0", "::", "ff02::1", "224.0.0.1", "fe80::1%eth0"):
            with self.assertRaises(ValueError):
                observer.Policy(endpoints=((ip, 3306),), candidate=True)
        with self.assertRaises(ValueError):
            self.policy(local_endpoints=(("127.0.0.1", 18080),))

    def test_duplicate_pending_cannot_hide_remote(self):
        result = observer.parse_trace([
            f'1 connect(3, {inet("198.51.100.1", 443)}, 16 <unfinished ...>',
            f'1 connect(4, {inet()}, 16 <unfinished ...>',
            '1 <... connect resumed>) = 0',
        ], self.policy())
        self.assertEqual(result["denied_count"], 1)
        self.assertTrue(result["parse_errors"])

    def test_payload_addresses_never_override_actual_target(self):
        fake = inet().replace('"', '\\"')
        result = observer.parse_trace([
            f'1 sendto(3, "{SECRET}, {fake}", 90, 0, {inet("198.51.100.1", 443)}, 16) = 90',
            f'1 sendmsg(3, {{msg_name=NULL, msg_iov=[{{iov_base="{SECRET}, {fake}", iov_len=90}}]}}, 0) = 90',
        ], self.policy())
        self.assertEqual(result["denied_count"], 2)
        self.assertTrue(SECRET not in json.dumps(result), "payload must not enter report")

    def test_unknown_lines_and_fields_cannot_leak_strings_or_pass(self):
        for line in [f'1 {SECRET}(4) = 0', f'1 connect(3, {{sa_family={SECRET}}}, 16) = 0',
                     f'1 connect(3, {inet()}, 16) = -1 {SECRET}',
                     f'1 sendmmsg(3, [{{msg_hdr={{msg_name=0x1234, secret="{SECRET}"}}}}], 1, 0) = 1']:
            result = observer.parse_trace([line], self.policy())
            self.assertTrue(result["parse_errors"])
            self.assertTrue(SECRET not in json.dumps(result), "raw unknown text must not enter report")

    def test_unknown_or_incomplete_observation_never_passes_full_report(self):
        policy = self.policy()
        for line in ('1 strange_syscall(4) = 0', '1 <... sendmmsg resumed>) = 2',
                     '1 io_uring_setup(1, 0x1234) = 3<anon_inode:[io_uring]>',
                     '1 sendmsg(3, {msg_name=NULL}, 0) = 4', '1 clone3(garbage) = 2'):
            parsed = observer.parse_trace([f'2 connect(3, {inet()}, 16) = 0', line], policy)
            report = observer.make_report(parsed, policy, 0)
            self.assertEqual(report["result"], "fail")
            self.assertIn("incomplete_observation", report["failures"])

    def test_no_inferred_peer_from_earlier_connect_or_explicit_opaque_address(self):
        result = observer.parse_trace([
            f'1 connect(3, {inet()}, 16) = 0',
            '1 sendto(3, ""..., 4, 0, NULL, 0) = 4',
            '1 sendto(3<TCP:[127.0.0.1:31000->127.0.0.1:18080]>, ""..., 4, 0, 0x1234, 16) = 4',
        ], self.policy())
        self.assertEqual(result["denied_count"], 2)

    def test_batch_reply_metadata_and_batch_disconnect_restrictions(self):
        policy = self.policy(local_endpoints=(("127.0.0.1", 18080),), reply_peer_ips=("127.0.0.1",))
        result = observer.parse_trace([
            '1 sendmmsg(3<TCP:[127.0.0.1:18080->127.0.0.1:31000]>, '
            + mmsg('NULL', inet(port=31000), '{sa_family=AF_UNSPEC}') + ', 3, 0) = 3',
        ], policy)
        self.assertEqual(result["denied_count"], 2)
        self.assertEqual(result["attempts"][0]["policy_basis"], "accepted_reply")

    def test_programmatic_trace_limits_are_fail_closed(self):
        for attribute, limit, lines in [
                ("MAX_TRACE_BYTES", 64, ['x' * 40, 'x' * 40]),
                ("MAX_ATTEMPTS", 1, [f'1 sendmmsg(3, {mmsg(inet(), inet())}, 2, 0) = 2'])]:
            with mock.patch.object(observer, attribute, limit):
                parsed = observer.parse_trace(lines, self.policy())
            self.assertIn("trace_limit_exceeded", parsed["parse_errors"])


class ParserTests(unittest.TestCase):
    def parse(self, *lines, broad=False, endpoints=(("127.0.0.1", 18080), ("::1", 18080))):
        return observer.parse_trace(lines, observer.Policy(endpoints=() if broad else endpoints, broad=broad))

    def test_exact_local_connect_allowed(self):
        result = self.parse(f'10 connect(3, {inet()}, 16) = 0')
        self.assertEqual((result["attempt_count"], result["denied_count"], result["parse_errors"]), (1, 0, {}))

    def test_failed_remote_attempt_denied(self):
        result = self.parse(f'10 connect(3, {inet("198.51.100.1", 443)}, 16) = -1 ENETUNREACH (Network is unreachable)')
        event = result["attempts"][0]
        self.assertEqual((result["denied_count"], event["return"], event["errno"]), (1, -1, "ENETUNREACH"))

    def test_redirect_second_connect_denied(self):
        result = self.parse(f'10 connect(3, {inet()}, 16) = 0',
                            f'11 connect(4, {inet("203.0.113.9", 443)}, 16) = -1 EINPROGRESS (Operation now in progress)')
        self.assertEqual(result["denied_count"], 1)

    def test_unknown_dns_sendto_denied_even_blocked(self):
        result = self.parse(f'11 sendto(7, ""..., 52, MSG_NOSIGNAL, {inet("192.0.2.53", 53)}, 16) = -1 ENETUNREACH (Network is unreachable)')
        self.assertEqual(result["denied_count"], 1)
        self.assertEqual((result["attempts"][0]["port"], result["attempts"][0]["syscall"]), (53, "sendto"))

    def test_unknown_loopback_dns_not_a_fixture(self):
        self.assertEqual(self.parse(f'11 sendto(7, ""..., 52, 0, {inet("127.0.0.53", 53)}, 16) = 52')["denied_count"], 1)

    def test_sendmsg_explicit_dns_destination(self):
        result = self.parse(f'12 sendmsg(7, {{msg_name={inet6("2001:db8::53", 53)}, msg_namelen=28, msg_iov=[{{iov_base=""..., iov_len=52}}], msg_iovlen=1}}, 0) = -1 ENETUNREACH (Network is unreachable)')
        self.assertEqual(result["denied_count"], 1)
        self.assertEqual(result["attempts"][0]["family"], "AF_INET6")

    def test_child_ipv6_connect_denied(self):
        result = self.parse(f'[pid 999] connect(5, {inet6("2001:db8::1", 443)}, 28) = -1 ENETUNREACH (Network is unreachable)')
        self.assertEqual((result["attempts"][0]["pid"], result["denied_count"]), (999, 1))

    def test_ipv6_loopback_exact_allowed(self):
        self.assertEqual(self.parse(f'999 connect(5, {inet6()}, 28) = 0')["denied_count"], 0)

    def test_wrong_fixture_port_denied(self):
        self.assertEqual(self.parse(f'10 connect(3, {inet(port=18081)}, 16) = 0')["denied_count"], 1)

    def test_unix_connect_allowed_without_path_in_report(self):
        result = self.parse(f'10 connect(3, {{sa_family=AF_UNIX, sun_path="{SECRET}"}}, 110) = 0')
        self.assertEqual(result["denied_count"], 0)
        self.assertTrue(SECRET not in json.dumps(result), "UNIX paths must not enter report")

    def test_connected_unix_sendmsg_allowed(self):
        result = self.parse('10 sendmsg(3<UNIX-STREAM:[10->11]>, {msg_name=NULL, msg_iov=[{iov_base=""..., iov_len=4}]}, 0) = 4')
        self.assertEqual(result["denied_count"], 0)

    def test_connected_tcp_null_sendto(self):
        result = self.parse('10 sendto(3<TCP:[127.0.0.1:31000->127.0.0.1:18080]>, ""..., 8, 0, NULL, 0) = 8')
        self.assertEqual((result["denied_count"], result["parse_errors"]), (0, {}))

    def test_inherited_ipv6_connected_sendmsg_denied(self):
        result = self.parse('102 sendmsg(3<TCPv6:[[::1]:31000->[2001:db8::2]:443]>, {msg_name=NULL, msg_iov=[{iov_base=""..., iov_len=4}]}, 0) = 4')
        self.assertEqual((result["denied_count"], result["attempts"][0]["ip"]), (1, "2001:db8::2"))

    def test_connected_udp_dns_null_sendto_denied(self):
        result = self.parse('102 sendto(3<UDP:[127.0.0.1:31000->192.0.2.53:53]>, ""..., 8, 0, NULL, 0) = -1 ENETUNREACH (Network is unreachable)')
        self.assertEqual(result["denied_count"], 1)

    def test_local_only_cached_udp_metadata_fails_closed(self):
        result = self.parse('102 sendto(3<UDP:[0.0.0.0:31000]>, ""..., 8, 0, NULL, 0) = 8', broad=True)
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("unresolved_destination", result["parse_errors"])

    def test_broad_mode_still_denies_unknown_loopback_dns_servers(self):
        for port in observer.RESOLVER_PORTS:
            result = self.parse(f'11 sendto(7, ""..., 52, 0, {inet(port=port)}, 16) = 52', broad=True)
            self.assertEqual(result["denied_count"], 1)

    def test_connected_ipv6_udp_local_sendmsg_allowed(self):
        result = self.parse('102 sendmsg(3<UDPv6:[[::1]:31000->[::1]:18080]>, {msg_name=NULL, msg_iov=[{iov_base=""..., iov_len=4}]}, 0) = 4')
        self.assertEqual(result["denied_count"], 0)

    def test_unresolved_null_send_fails_closed(self):
        result = self.parse('10 sendto(3, ""..., 4, 0, NULL, 0) = 4')
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("unresolved_destination", result["parse_errors"])

    def test_opaque_sockaddr_fails_closed(self):
        result = self.parse('10 connect(3, 0x123456, 16) = -1 EFAULT (Bad address)')
        self.assertEqual(result["denied_count"], 1)

    def test_unknown_family_fails_closed(self):
        self.assertEqual(self.parse('10 connect(3, {sa_family=AF_NETLINK, nl_pid=0}, 12) = 0')["denied_count"], 1)

    def test_unfinished_interleaved_threads(self):
        result = self.parse(f'10 connect(3, {inet()}, 16 <unfinished ...>',
                            f'11 connect(4, {inet("203.0.113.1", 443)}, 16) = -1 ENETUNREACH (Network is unreachable)',
                            '10 <... connect resumed>) = 0')
        self.assertEqual((result["attempt_count"], result["denied_count"], result["parse_errors"]), (2, 1, {}))

    def test_unfinished_remote_still_denied_and_incomplete(self):
        result = self.parse(f'10 connect(3, {inet("203.0.113.1", 443)}, 16 <unfinished ...>')
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("incomplete_syscall", result["parse_errors"])

    def test_orphan_resumed_fails_closed(self):
        self.assertIn("orphan_resumed_syscall", self.parse('10 <... connect resumed>) = 0')["parse_errors"])

    def test_malformed_result_still_records_remote(self):
        result = self.parse(f'10 connect(3, {inet("203.0.113.1", 443)}, 16) = garbage')
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("unparsed_syscall_result", result["parse_errors"])

    def test_payload_text_is_never_copied_to_report(self):
        result = self.parse(f'10 sendto(3, "{SECRET}", 64, 0, {inet()}, 16) = 64')
        self.assertTrue(SECRET not in json.dumps(result), "payload must not enter report")

    def test_broad_policy_explicit_and_not_all_loopback_addresses(self):
        result = self.parse(f'10 connect(3, {inet(port=45454)}, 16) = 0',
                            f'11 connect(4, {inet("127.0.0.2", 45454)}, 16) = 0', broad=True)
        self.assertEqual(result["denied_count"], 1)
        self.assertIn("ANY non-DNS port", observer.Policy(broad=True).summary()["port_coverage"])

    def test_accepted_socket_ephemeral_peer_needs_explicit_port(self):
        result = self.parse('10 sendto(3<TCP:[127.0.0.1:18080->127.0.0.1:31000]>, ""..., 8, 0, NULL, 0) = 8')
        self.assertEqual(result["denied_count"], 1)

    def test_trace_limits_fail_closed(self):
        self.assertIn("trace_limit_exceeded", self.parse("x" * (observer.MAX_LINE_BYTES + 1))["parse_errors"])

    def test_terminal_noise_ignored(self):
        result = self.parse('10 +++ exited with 0 +++', '11 --- SIGTERM {si_signo=SIGTERM} ---')
        self.assertEqual(result["parse_errors"], {})


class HarnessTests(unittest.TestCase):
    def test_strace_records_only_requested_calls_and_zero_string_bytes(self):
        argv = observer.trace_argv(["python", "private-argv"], Path("/tmp/trace"))
        self.assertIn("-f", argv)
        self.assertEqual(argv[argv.index("-s") + 1], "0")
        self.assertIn("trace=" + observer.SYSCALLS, argv)
        self.assertEqual(set(observer.SYSCALLS.split(",")),
                         observer.NETWORK_CALLS | observer.URING_CALLS | observer.PROCESS_CALLS)
        self.assertIn("-yy", argv)
        self.assertIn("-v", argv)
        self.assertNotIn("execve", " ".join(argv))

    def test_environment_drops_keys_proxies_and_hooks(self):
        with mock.patch.dict(os.environ, {"API_KEY": SECRET, "HTTPS_PROXY": SECRET, "PYTHONPATH": SECRET}):
            env = observer.clean_environment("/tmp/public")
        self.assertTrue(SECRET not in json.dumps(env), "inherited secrets must be dropped")

    def test_manifest_exact_and_ipv6_canonicalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ports.json"
            path.write_text(json.dumps({"endpoints": [{"ip": "0:0:0:0:0:0:0:1", "port": 18080}]}))
            policy = observer.load_policy(path)
        self.assertTrue(policy.allows("AF_INET6", "::1", 18080))
        self.assertFalse(policy.allows("AF_INET6", "::1", 18081))

    def test_invalid_manifests_rejected(self):
        bad = [[], {}, {"endpoints": []}, {"endpoints": [{"ip": "localhost", "port": 80}]},
               {"endpoints": [{"ip": "203.0.113.1", "port": 443}]},
               {"endpoints": [{"ip": "127.0.0.1", "port": 0}]},
               {"endpoints": [{"ip": "127.0.0.1", "port": True}]},
               {"endpoints": [{"ip": "127.0.0.1", "port": "80"}]},
               {"endpoints": [{"ip": "127.0.0.1", "port": 80, "allow": "all"}]}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ports.json"
            for data in bad:
                path.write_text(json.dumps(data))
                with self.assertRaises(observer.ObservationError):
                    observer.load_policy(path)

    def test_child_failure_never_masked_by_allowed_traffic(self):
        policy = observer.Policy(broad=True)
        parsed = observer.parse_trace([f'10 connect(3, {inet()}, 16) = 0'], policy)
        result = observer.make_report(parsed, policy, 7)
        self.assertEqual((result["result"], result["command_returncode"]), ("fail", 7))
        self.assertIn("command_failed", result["failures"])

    def test_empty_trace_not_pass(self):
        policy = observer.Policy(broad=True)
        result = observer.make_report(observer.parse_trace([], policy), policy, 0)
        self.assertIn("no_inet_attempts_observed", result["failures"])

    def test_network_none_enforced_before_spawn(self):
        with mock.patch.object(observer, "loopback_namespace", return_value=False), mock.patch.object(subprocess, "Popen") as spawn:
            with self.assertRaises(observer.ObservationError):
                observer.observe(["anything"], timeout=1, broad=True)
            spawn.assert_not_called()

    def test_cli_setup_failure_sanitized_and_nonzero(self):
        output = io.StringIO()
        with mock.patch.object(observer, "loopback_namespace", side_effect=OSError(SECRET)), contextlib.redirect_stdout(output):
            rc = observer.main(["--network-none", "--fixture-loopback-only", "--", "anything"])
        self.assertEqual(rc, 1)
        self.assertTrue(SECRET not in output.getvalue(), "exception text must not enter report")

    def test_timeout_kills_detached_tracees_before_tracer(self):
        process = mock.Mock(pid=120)
        calls = []
        with mock.patch.object(observer, "tracee_pids", return_value={121, 122}), \
                mock.patch.object(os, "kill", side_effect=lambda pid, sig: calls.append(("child", pid))), \
                mock.patch.object(os, "killpg", side_effect=lambda pid, sig: calls.append(("group", pid))):
            observer.stop_tracees(process)
        self.assertEqual(set(calls[:-1]), {("child", 121), ("child", 122)})
        self.assertEqual(calls[-1], ("group", 120))

    def test_network_none_allows_down_fallback_tunnels_but_not_active_interfaces_or_routes(self):
        files = {"/sys/class/net/lo/flags": "0x9", "/sys/class/net/gre0/flags": "0x80",
                 "/proc/net/route": "Iface Destination\n", "/proc/net/ipv6_route": "0000 lo\n"}
        with mock.patch.object(sys, "platform", "linux"), \
                mock.patch.object(observer.socket, "if_nameindex", return_value=[(1, "lo"), (2, "gre0")]), \
                mock.patch.object(Path, "read_text", new=lambda path: files[str(path)]):
            self.assertTrue(observer.loopback_namespace())
            files["/sys/class/net/gre0/flags"] = "0x81"
            self.assertFalse(observer.loopback_namespace())
            files["/sys/class/net/gre0/flags"] = "0x80"
            files["/proc/net/route"] += "gre0 0000\n"
            self.assertFalse(observer.loopback_namespace())
            files["/proc/net/route"] = "Iface Destination\n"
            files["/proc/net/ipv6_route"] = "0000 gre0\n"
            self.assertFalse(observer.loopback_namespace())


class LiveStraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        available = sys.platform == "linux" and shutil.which("strace") and observer.loopback_namespace()
        if not available:
            if os.environ.get("EGRESS_REQUIRE_STRACE") == "1":
                raise RuntimeError("live_strace_requires_linux_strace_and_network_none")
            raise unittest.SkipTest("live strace requires isolated Linux --network none; parser tests still run")

    def test_candidate_accepted_reply_and_epoch_from_real_socket_metadata(self):
        code = '''import json, socket, sys
listener = socket.socket()
listener.bind(("127.0.0.1", 0)); listener.listen(1)
open(sys.argv[1], "w").write(json.dumps(listener.getsockname()))
client = socket.socket(); client.connect(listener.getsockname())
accepted, _ = listener.accept()
accepted.send(b"reply"); accepted.sendmsg([b"reply"])
'''
        with tempfile.TemporaryDirectory() as directory:
            trace, manifest = Path(directory) / "trace", Path(directory) / "listener.json"
            argv = observer.trace_argv([sys.executable, "-B", "-c", code, str(manifest)], trace)
            argv.insert(1, "-ttt")
            result = subprocess.run(argv, env=observer.clean_environment(directory),
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=10)
            self.assertEqual(result.returncode, 0, "isolated accepted-reply trace failed")
            listener = tuple(json.loads(manifest.read_text()))
            policy = observer.Policy(endpoints=(listener,), candidate=True,
                                     local_endpoints=(listener,), reply_peer_ips=("127.0.0.1",))
            parsed = observer.parse_trace(trace.read_text().splitlines(), policy)
        self.assertEqual((parsed["denied_count"], parsed["parse_errors"]), (0, {}))
        replies = [e for e in parsed["attempts"] if e["policy_basis"] == "accepted_reply"]
        self.assertGreaterEqual(len(replies), 2, "real accepted sends need the listener-direction policy")
        self.assertTrue(all(e.get("timestamp", 0) > 1e9 for e in parsed["attempts"]))

    def test_real_sendmmsg_full_vector_and_partial_failure_fail_closed(self):
        code = '''import ctypes, json, socket, struct, sys
class Iovec(ctypes.Structure):
    _fields_ = [("base", ctypes.c_void_p), ("length", ctypes.c_size_t)]
class Msghdr(ctypes.Structure):
    _fields_ = [("name", ctypes.c_void_p), ("namelen", ctypes.c_uint),
                ("iov", ctypes.POINTER(Iovec)), ("iovlen", ctypes.c_size_t),
                ("control", ctypes.c_void_p), ("controllen", ctypes.c_size_t), ("flags", ctypes.c_int)]
class Mmsghdr(ctypes.Structure):
    _fields_ = [("hdr", Msghdr), ("length", ctypes.c_uint)]
receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver.bind(("127.0.0.1", 0))
port = receiver.getsockname()[1]
open(sys.argv[1], "w").write(json.dumps(["127.0.0.1", port]))
sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
payload = ctypes.create_string_buffer(sys.argv[2].encode())
iov = Iovec(ctypes.cast(payload, ctypes.c_void_p), len(sys.argv[2]))
libc = ctypes.CDLL(None, use_errno=True)
for second_ip in ("127.0.0.1", "198.51.100.1"):
    addresses = [ctypes.create_string_buffer(struct.pack("=H", socket.AF_INET) + struct.pack("!H", port)
                 + socket.inet_aton(ip) + b"\\x00" * 8) for ip in ("127.0.0.1", second_ip)]
    messages = (Mmsghdr * 2)()
    for i, address in enumerate(addresses):
        messages[i].hdr = Msghdr(ctypes.cast(address, ctypes.c_void_p), 16, ctypes.pointer(iov), 1, None, 0, 0)
    returned = libc.sendmmsg(sender.fileno(), messages, 2, 0)
    if second_ip == "127.0.0.1": assert returned == 2
'''
        with tempfile.TemporaryDirectory() as directory:
            trace, manifest = Path(directory) / "trace", Path(directory) / "endpoint.json"
            result = subprocess.run(observer.trace_argv(
                [sys.executable, "-B", "-c", code, str(manifest), SECRET], trace),
                env=observer.clean_environment(directory), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            self.assertEqual(result.returncode, 0, "isolated libc.sendmmsg fixture failed")
            policy = observer.Policy(endpoints=(tuple(json.loads(manifest.read_text())),), candidate=True)
            raw = trace.read_text()
            self.assertTrue(SECRET not in raw, "sendmmsg trace must not contain payload")
            lines = raw.splitlines()
            successful = [line for line in lines if 'sendmmsg(' in line and line.endswith('= 2')]
            self.assertTrue(successful, "must observe a full sendmmsg vector")
            clean = observer.parse_trace(successful, policy)
            self.assertEqual((clean["attempt_count"], clean["denied_count"], clean["parse_errors"]), (2, 0, {}))
            parsed = observer.parse_trace(lines, policy)
        self.assertGreaterEqual(parsed["denied_count"], 1, "partial failed batch must not hide remote destination")
        self.assertTrue(SECRET not in json.dumps(parsed), "sendmmsg report must not contain payload")

    def test_kernel_netlink_and_unspec_disconnect_real_encoding(self):
        code = '''import ctypes, socket, struct
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("127.0.0.1", 18080))
addr = ctypes.create_string_buffer(struct.pack("=H", socket.AF_UNSPEC) + b"\\x00" * 14)
assert ctypes.CDLL(None).connect(s.fileno(), addr, 16) == 0
n = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, socket.NETLINK_ROUTE)
n.connect((0, 0))
n.sendto(struct.pack("=IHHII", 16, 18, 0, 1, 0), (0, 0))
'''
        report = observer.observe([sys.executable, "-B", "-c", code], timeout=10, broad=True)
        self.assertEqual(report["result"], "pass", "kernel-only netlink and UDP disconnect must parse cleanly")
        self.assertTrue({"kernel_netlink", "unspec_disconnect"} <= {e["policy_basis"] for e in report["attempts"]})

    def test_zero_string_length_really_hides_secret_in_trace_and_report(self):
        # Real UDP sendto plus TCP connect/send/scatter-gather sendmsg in a
        # worker thread. No actual secret or raw trace enters test failure text.
        code = '''import socket, sys, threading
r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.bind(("127.0.0.1", 0))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
secret = sys.argv[1].encode()
s.sendto(secret, r.getsockname())
listener = socket.socket()
listener.bind(("127.0.0.1", 0)); listener.listen(1)
client = socket.socket()
client.connect(listener.getsockname())
accepted, _ = listener.accept()
client.send(secret)
t = threading.Thread(target=lambda: client.sendmsg([secret, secret]))
t.start(); t.join()
'''
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "network.trace"
            result = subprocess.run(observer.trace_argv([sys.executable, "-B", "-c", code, SECRET], trace),
                                    env=observer.clean_environment(directory), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            self.assertEqual(result.returncode, 0, "strace failed; retry only with SYS_PTRACE if needed")
            raw = trace.read_text()
            self.assertTrue(SECRET not in raw, "synthetic secret leaked into trace")
            parsed = observer.parse_trace(raw.splitlines(), observer.Policy(broad=True))
            report = observer.make_report(parsed, observer.Policy(broad=True), result.returncode)
            self.assertTrue(SECRET not in json.dumps(report), "synthetic secret leaked into report")
            self.assertEqual(report["result"], "pass", "live zero-payload trace must parse cleanly")
            self.assertTrue({"connect", "sendto", "sendmsg"} <= {e["syscall"] for e in parsed["attempts"]})
            self.assertGreaterEqual(len({e["pid"] for e in parsed["attempts"]}), 2, "thread traffic must be followed")

    def test_blocked_child_and_thread_attempts_still_fail(self):
        code = '''import socket, subprocess, sys, threading
def attempt(family, address):
    s = socket.socket(family)
    try: s.connect(address)
    except OSError: pass
    finally: s.close()
child = "import socket; s=socket.socket(); s.connect_ex(('198.51.100.8',443))"
subprocess.run([sys.executable, "-B", "-c", child], check=True)
t = threading.Thread(target=attempt, args=(socket.AF_INET6, ("2001:db8::8",443)))
t.start(); t.join()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try: s.sendto(b"synthetic-dns", ("192.0.2.53",53))
except OSError: pass
'''
        report = observer.observe([sys.executable, "-B", "-c", code], timeout=10, broad=True)
        self.assertEqual(report["command_returncode"], 0)
        self.assertEqual(report["result"], "fail")
        self.assertGreaterEqual(report["denied_count"], 3)
        self.assertTrue(any(e["family"] == "AF_INET6" for e in report["attempts"]))
        self.assertTrue(any(e["port"] == 53 and not e["allowed"] for e in report["attempts"]))

    def test_actual_failed_turn_exit_is_preserved(self):
        code = 'import socket, sys; s=socket.socket(); s.connect_ex(("127.0.0.1",18080)); sys.exit(7)'
        report = observer.observe([sys.executable, "-B", "-c", code], timeout=10, broad=True)
        self.assertEqual((report["result"], report["command_returncode"]), ("fail", 7))
        self.assertEqual(report["denied_count"], 0)

    def test_dynamic_fixture_manifest_read_after_command(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dynamic-ports.json"
            code = '''import json, socket, sys
r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.bind(("127.0.0.1",0))
open(sys.argv[1], "w").write(json.dumps({"endpoints":[{"ip":"127.0.0.1","port":r.getsockname()[1]}]}))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"synthetic",r.getsockname())
'''
            report = observer.observe([sys.executable, "-B", "-c", code, str(path)], timeout=10, fixture_ports=path)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["policy"]["mode"], "exact_fixture_endpoints")

    def test_timeout_fails_even_if_no_egress(self):
        report = observer.observe([sys.executable, "-B", "-c", "import time; time.sleep(30)"], timeout=0.2, broad=True)
        self.assertEqual(report["result"], "fail")
        self.assertIn("command_timeout", report["failures"])

    def test_timeout_kills_child_in_separate_session(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "child-pid"
            code = '''import subprocess, sys, time
p = subprocess.Popen([sys.executable,"-B","-c","import time; time.sleep(30)"], start_new_session=True)
open(sys.argv[1],"w").write(str(p.pid))
time.sleep(30)
'''
            report = observer.observe([sys.executable, "-B", "-c", code, str(path)], timeout=0.5, broad=True)
            self.assertTrue(path.is_file(), "detached test child must have started")
            pid = int(path.read_text())
            status = Path(f"/proc/{pid}/status")
            if status.exists():
                text = status.read_text()
                state = next(line for line in text.splitlines() if line.startswith("State:"))
                self.assertTrue("Z (zombie)" in state or "X (dead)" in state, "detached child must not remain running")
        self.assertIn("command_timeout", report["failures"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
