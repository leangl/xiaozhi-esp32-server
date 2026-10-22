#!/usr/bin/env python3
r"""Bounded external syscall observer for service-removal smoke, not a sandbox.

Linux runner MUST use Docker --network none, disposable /tmp, no deployment
mounts, credentials, .env, data, paid calls or existing stack. Add SYS_PTRACE
only if the default container profile prevents tracing; never use privileged
or disable seccomp wholesale. Source-only unit tests also run on macOS.

Build only after approval, from the repository root, with public tools only:

    set -o pipefail
    COPYFILE_DISABLE=1 tar --no-xattrs -cf - tools/Dockerfile-egress-observer \
      tools/service-egress-check.py tools/service-egress-check.test.py | \
      docker build --pull=false --build-arg OWNED_BASE=xiaozhi-policy/server-base:20261021 \
        -f tools/Dockerfile-egress-observer -t xiaozhi-policy/egress-observer:20261021 -

Test runner (no mounts; live tests must not skip):

    docker run --rm --init --network none --read-only --cap-drop ALL \
      --tmpfs /tmp:rw,nosuid,nodev,size=1g --pids-limit 512 \
      xiaozhi-policy/egress-observer:20261021 \
      python -B /opt/egress-observer/service-egress-check.test.py

Actual current voice smoke, public source/test tool/reviewed model only; no mounts:

    {
      printf '%s\n' tools/service-voice-smoke.py \
        main/xiaozhi-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx
      rg --files -g '*.py' main/xiaozhi-server/config main/xiaozhi-server/core \
        main/xiaozhi-server/plugins_func
    } | COPYFILE_DISABLE=1 tar --no-xattrs -cf - -T - | \
      docker run --rm -i --init --network none --read-only --cap-drop ALL \
        --tmpfs /tmp:rw,nosuid,nodev,size=1g --pids-limit 512 --cpus 2 \
        xiaozhi-policy/egress-observer:20261021 sh -ec '
          mkdir /tmp/public-source
          tar --no-same-owner -xf - -C /tmp/public-source
          exec python -B /opt/egress-observer/service-egress-check.py \
            --network-none --fixture-loopback-only --timeout 150 -- \
            python -B /tmp/public-source/tools/service-voice-smoke.py \
              --source-root /tmp/public-source/main/xiaozhi-server \
              --vad-model models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx \
              --timeout 120'

For another bounded fixture command, the invocation inside that container is:

    python -B /opt/egress-observer/service-egress-check.py \
      --network-none --fixture-loopback-only --timeout 90 -- \
      python -B /fixtures/service-voice-smoke.py \
        --source-root /fixtures/server --vad-model /fixtures/silero_vad.onnx

The current voice smoke allocates dynamic ports without exporting them. The
explicit --fixture-loopback-only fallback permits ANY non-DNS port on exactly
127.0.0.1 and ::1, only in a verified loopback-only namespace. Resolver ports
53/853/5353/5355 are denied without an exact manifest. This is broader port
coverage, NOT an exact fixture-port proof. No other 127/8 address is allowed.

Prefer --fixture-ports /tmp/fixture-ports.json once the fixture exports:
    {"endpoints": [{"ip": "127.0.0.1", "port": 12345}]}
The file is read AFTER the command, so the fixture can publish dynamic ports.
Only numeric loopback IPs and ports 1..65535 are accepted. All destination ports
(including accepted sockets' ephemeral peers) must be listed in this legacy mode.
No fixture is imported, patched or instrumented by this utility.
Fixed management fixture endpoints can list 127.0.0.1:19200/8000/18000; observing
the client alone does NOT observe a separately started candidate or gateway.

strace follows children/threads with -f and records connect/sendto/sendmsg/sendmmsg,
clone/fork bookkeeping, and io_uring setup/enter/register. Only setup probes
refused by the kernel with EPERM/EACCES/ENOSYS are safe non-I/O events; usable
rings, submission calls and ambiguous failures fail closed.
It uses -s 0 (zero payload bytes), unabbreviated vectors, socket metadata, and
no signal data. The private
temporary trace is deleted; raw lines, UNIX paths, argv, stdout/stderr, payloads
and exception text are never put in the report. Child output is discarded, but
ANY nonzero exit or timeout fails the wrapper, independently of egress policy.
Bookworm strace 6.1 has no --kill-on-exit: timeout cleanup finds descendants and
attached tracees through /proc, including separate sessions. Always use a
disposable container (--init recommended) as the outer cleanup boundary.

All observed unapproved attempts fail, including ENETUNREACH/ECONNREFUSED and
DNS sendto/sendmsg to unknown servers. There is NO hostname/DNS-question witness:
DNS operator names, DoH names, redirects not exercised by the command,
inherited/pre-existing untraced processes, and management/gateway scenarios are
untested by this CLI. This utility does not complete all of section 7.1.
Unresolved connected sends fail closed; Bookworm may show cached local-only UDP
metadata. No destination is inferred from a reused fd or a local source port.

Programmatic candidate parsing is opt-in: Policy(endpoints=reviewed_pairs,
candidate=True). Only this mode accepts numeric nonloopback exact endpoints.
Optional local_endpoints=reviewed_listener_pairs and reply_peer_ips=reviewed_ips
allow connected TCP NULL-send replies only when trusted -yy local->peer metadata
matches both lists. They never authorize connect, UDP, or explicit destinations.
No policy supplies a subnet or an ephemeral destination-port range. parse_trace
does not verify a namespace or process identity; the caller owns trace provenance,
candidate isolation, and capture completeness. Reject denied_count OR parse_errors.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import errno
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time


MAX_TRACE_BYTES = 8 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_ATTEMPTS = 10000
NETWORK_CALLS = frozenset({"connect", "sendto", "sendmsg", "sendmmsg"})
URING_CALLS = frozenset({"io_uring_setup", "io_uring_enter", "io_uring_register"})
PROCESS_CALLS = frozenset({"clone", "clone3", "fork", "vfork"})
SYSCALLS = "connect,sendto,sendmsg,sendmmsg,io_uring_setup,io_uring_enter,io_uring_register,clone,clone3,fork,vfork"
# Whitelist labels; never copy arbitrary result text into a sanitized report.
ERRNOS = frozenset(errno.errorcode.values()) | {
    "ERESTARTSYS", "ERESTARTNOINTR", "ERESTARTNOHAND", "ERESTART_RESTARTBLOCK",
    "ENONET", "EUCLEAN", "EREMOTEIO", "EHWPOISON", "ENOKEY", "EKEYEXPIRED",
    "EKEYREVOKED", "EKEYREJECTED", "ERFKILL", "ENOMEDIUM", "EMEDIUMTYPE",
}
RESOLVER_PORTS = {53, 853, 5353, 5355}
LIMITS = [
    "Numeric IP/port observation only; DNS questions and operator hostnames untested.",
    "Connect/sendto/sendmsg/sendmmsg in the supplied command and ordinary descendants only.",
    "Not adversarial containment; usable/submitted io_uring fails closed; only kernel-refused setup probes are non-I/O events.",
    "Unresolved connected sends fail closed; cached local-only UDP metadata is insufficient.",
    "Only the exercised smoke path; full management/gateway and section 7.1 incomplete.",
]


class ObservationError(Exception):
    """Messages are fixed public event labels, never external exception text."""


def endpoint(ip, port):
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid_endpoint")
    return numeric_ip(ip), port


def numeric_ip(ip):
    try:
        if not isinstance(ip, str) or "%" in ip:
            raise ValueError()
        address = ipaddress.ip_address(ip)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if address.is_unspecified or address.is_multicast or str(address) == "255.255.255.255":
            raise ValueError()
        return str(address)
    except ValueError:
        raise ValueError("invalid_endpoint") from None


class Policy:
    def __init__(self, endpoints=(), broad=False, *, candidate=False,
                 local_endpoints=(), reply_peer_ips=()):
        if type(candidate) is not bool or type(broad) is not bool:
            raise ValueError("invalid_policy_mode")
        self.broad = broad
        self.candidate = candidate
        self.endpoints = frozenset(endpoint(ip, port) for ip, port in endpoints)
        self.local_endpoints = frozenset(endpoint(ip, port) for ip, port in local_endpoints)
        self.reply_peer_ips = frozenset(numeric_ip(ip) for ip in reply_peer_ips)
        if not candidate and any(not ipaddress.ip_address(ip).is_loopback for ip, _ in self.endpoints):
            raise ValueError("fixture_must_be_loopback")
        if not candidate and (self.local_endpoints or self.reply_peer_ips):
            raise ValueError("candidate_reply_mode_required")
        if bool(self.local_endpoints) != bool(self.reply_peer_ips):
            raise ValueError("reply_listener_and_peer_ips_required")
        if broad and (self.endpoints or candidate):
            raise ValueError("ambiguous_policy")

    def allows(self, family, ip, port):
        if family == "AF_UNIX":
            return True
        if family not in {"AF_INET", "AF_INET6"} or ip is None:
            return False
        try:
            ip, port = endpoint(ip, port)
        except ValueError:
            return False
        return ((ip in {"127.0.0.1", "::1"} and port not in RESOLVER_PORTS) if self.broad
                else (ip, port) in self.endpoints)

    def allows_reply(self, local, peer):
        return (self.candidate and local in self.local_endpoints
                and peer is not None and peer[0] in self.reply_peer_ips)

    def summary(self):
        return {
            "mode": ("fixture_loopback_any_port" if self.broad else
                     "exact_candidate_endpoints" if self.candidate else "exact_fixture_endpoints"),
            "port_coverage": ("ANY non-DNS port on 127.0.0.1 and ::1; 53/853/5353/5355 denied" if self.broad else
                              "exact listed destination ports; TCP replies from exact local listener and peer-IP pairs" if self.local_endpoints else
                              "exact listed destination ports"),
            "endpoints": [{"ip": ip, "port": port} for ip, port in sorted(self.endpoints)],
            "local_reply_endpoints": [{"ip": ip, "port": port} for ip, port in sorted(self.local_endpoints)],
            "reply_peer_ips": sorted(self.reply_peer_ips),
            "af_unix_allowed": True,
            "af_netlink_kernel_unicast_allowed": True,
            "af_unspec_connect_disconnect_allowed": True,
        }


def load_policy(path):
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ObservationError("invalid_fixture_manifest")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if set(data) != {"endpoints"} or not isinstance(data["endpoints"], list):
            raise ValueError()
        items = data["endpoints"]
        if not items or any(not isinstance(item, dict) or set(item) != {"ip", "port"} for item in items):
            raise ValueError()
        return Policy((item["ip"], item["port"]) for item in items)
    except (ValueError, TypeError, KeyError):
        raise ObservationError("invalid_fixture_manifest") from None


def loopback_namespace():
    """No active non-loopback interface or non-loopback IPv4/IPv6 route.

    Docker Desktop also exposes DOWN kernel fallback tunnel devices in a
    --network none namespace. These cannot be raised with our cap-drop runner.
    """
    if sys.platform != "linux":
        return False
    interfaces = {name for _, name in socket.if_nameindex()}
    if "lo" not in interfaces:
        return False
    for name in interfaces:
        flags = int((Path("/sys/class/net") / name / "flags").read_text().strip(), 16)
        if name != "lo" and flags & 1:  # IFF_UP
            return False
    routes4 = Path("/proc/net/route").read_text().splitlines()[1:]
    routes6 = Path("/proc/net/ipv6_route").read_text().splitlines()
    return (all(line.split()[0] == "lo" for line in routes4 if line.strip())
            and all(line.split()[-1] == "lo" for line in routes6 if line.strip()))


def trace_argv(command, trace_path):
    return ["strace", "-f", "-qq", "-s", "0", "-v",
            "-e", "trace=" + SYSCALLS, "-e", "signal=none",
            "-yy", "-o", str(trace_path), "--", *command]


def clean_environment(home):
    # Do not propagate keys, proxy settings, Python hooks, user config or .env.
    return {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(home),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
            "NO_PROXY": "127.0.0.1,::1,localhost", "no_proxy": "127.0.0.1,::1,localhost"}


def tracee_pids(tracer_pid):
    """Numeric process metadata only; never inspect argv, environ or data."""
    relations = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal():
            continue
        try:
            fields = {}
            for line in (path / "status").read_text().splitlines():
                name, _, value = line.partition(":")
                if name in {"PPid", "TracerPid"}:
                    fields[name] = int(value.strip())
            relations[int(path.name)] = fields
        except (FileNotFoundError, ProcessLookupError):
            continue  # A tracee can exit during enumeration.
    selected = {tracer_pid}
    while True:
        found = {pid for pid, fields in relations.items()
                 if fields.get("PPid") in selected or fields.get("TracerPid") == tracer_pid}
        if found <= selected:
            return selected - {tracer_pid}
        selected.update(found)


def stop_tracees(process):
    # Kill tracees before the tracer, so setsid() cannot evade group cleanup.
    # This is bounded trusted-fixture cleanup, not adversarial process isolation.
    try:
        for pid in tracee_pids(process.pid):
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def split_arguments(text):
    """Split only structural commas, never commas/addresses inside payloads.

    The angle-bracket state handles -yy fd metadata, including its -> arrow.
    No quoted string is decoded, stored in an event, or searched for addresses.
    """
    parts, stack = [], []
    quote, escaped, metadata, start = None, False, False, 0
    pairs = {"(": ")", "[": "]", "{": "}"}
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif metadata:
            if char == ">" and (index == 0 or text[index - 1] != "-"):
                metadata = False
        elif char == "<":
            metadata = True
        elif char in pairs:
            stack.append(pairs[char])
        elif char in ")]}":
            if not stack or stack.pop() != char:
                return None
        elif char == "," and not stack:
            parts.append(text[start:index].strip())
            start = index + 1
    if quote or stack or metadata:
        return None
    parts.append(text[start:].strip())
    return parts if all(parts) else ([] if not text.strip() else None)


def struct_fields(text):
    if not (text.startswith("{") and text.endswith("}")):
        return None
    parts = split_arguments(text[1:-1])
    if parts is None:
        return None
    fields = {}
    for part in parts:
        if part.startswith("inet_pton("):
            key, value = "inet_pton", part
        else:
            key, separator, value = part.partition("=")
            if not separator or not re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", key.strip()):
                return None
            key, value = key.strip(), value.strip()
        if key in fields or not value:
            return None
        fields[key] = value
    return fields


UNKNOWN_TARGET = ("unknown", None, None, "unresolved")


def sockaddr(text):
    fields = struct_fields(text)
    if fields is None:
        return UNKNOWN_TARGET
    family = fields.get("sa_family")
    if family == "AF_UNIX":
        return family, None, None, "unix"
    if family == "AF_UNSPEC":
        return family, None, None, "disconnect"
    if family == "AF_NETLINK":
        # A nonzero port-id addresses a userspace peer; groups may multicast
        # to userspace. Missing/truncated fields cannot establish kernel-only.
        zero = r"(?:0+|0x0+)"
        kernel = all(re.fullmatch(zero, fields.get(key, "")) for key in ("nl_pid", "nl_groups"))
        return family, None, None, "kernel_netlink" if kernel else "unresolved"
    if family == "AF_INET":
        ip = re.fullmatch(r'inet_addr\("([0-9.]+)"\)', fields.get("sin_addr", ""))
        port = re.fullmatch(r"htons\(([0-9]{1,5})\)", fields.get("sin_port", ""))
    elif family == "AF_INET6":
        ip = re.fullmatch(r'inet_pton\(AF_INET6,\s*"([0-9a-fA-F:.]+)",\s*&sin6_addr\)',
                          fields.get("inet_pton", fields.get("sin6_addr", "")))
        port = re.fullmatch(r"htons\(([0-9]{1,5})\)", fields.get("sin6_port", ""))
        if fields.get("sin6_scope_id", "0") != "0":
            return UNKNOWN_TARGET
    else:
        return UNKNOWN_TARGET
    if ip and port:
        try:
            if ipaddress.ip_address(ip[1]).version != (4 if family == "AF_INET" else 6):
                return UNKNOWN_TARGET
            numeric, number = endpoint(ip[1], int(port[1]))
            return family, numeric, number, "endpoint"
        except ValueError:
            pass
    return UNKNOWN_TARGET


def socket_metadata(fd):
    """Only trusted kernel-produced -yy local->peer pairs, never fd history."""
    match = re.fullmatch(r"[0-9]{1,10}<(TCPv6|UDPv6|TCP|UDP|UNIX(?:-STREAM|-DGRAM|-SEQPACKET)?):\[(.*)\]>", fd)
    if not match:
        return None, None, None, None
    transport, addresses = match.groups()
    if transport.startswith("UNIX"):
        return "AF_UNIX", None, None, transport
    if addresses.count("->") != 1:
        return None, None, None, None
    ipv6 = transport.endswith("v6")
    parsed = []
    for text in addresses.split("->"):
        pair = re.fullmatch(r"\[([0-9a-fA-F:.]+)\]:([0-9]{1,5})" if ipv6
                            else r"([0-9.]+):([0-9]{1,5})", text)
        if not pair:
            return None, None, None, None
        try:
            if ipaddress.ip_address(pair[1]).version != (6 if ipv6 else 4):
                return None, None, None, None
            parsed.append(endpoint(pair[1], int(pair[2])))
        except ValueError:
            return None, None, None, None
    return "AF_INET6" if ipv6 else "AF_INET", parsed[0], parsed[1], transport


def call_targets(name, args, errors):
    """Return every attempted destination, including failed sendmmsg entries."""
    parts = split_arguments(args)
    expected = {"connect": 3, "sendto": 6, "sendmsg": 3, "sendmmsg": 4}[name]
    if parts is None or len(parts) != expected:
        errors["unparsed_syscall_arguments"] += 1
        return [(UNKNOWN_TARGET, None, None, None)]
    family, local, peer, transport = socket_metadata(parts[0])

    def target(text, connected=False):
        if connected and text == "NULL":
            if family == "AF_UNIX":
                return (family, None, None, "unix"), local, peer, transport
            if peer:
                return (family, *peer, "connected"), local, peer, transport
            return UNKNOWN_TARGET, local, peer, transport
        # Explicit sockaddr ALWAYS wins over metadata, even when unreadable.
        return sockaddr(text), local, peer, None

    if name == "connect":
        return [target(parts[1])]
    if name == "sendto":
        return [target(parts[4], connected=True)]
    if name == "sendmsg":
        header = struct_fields(parts[1])
        return [target(header.get("msg_name", "") if header else "", connected=True)]
    vector, count = parts[1:3]
    if not re.fullmatch(r"[0-9]{1,5}", count) or not vector.startswith("[") or not vector.endswith("]"):
        errors["unparsed_sendmmsg_vector"] += 1
        return [(UNKNOWN_TARGET, local, peer, None)]
    messages = split_arguments(vector[1:-1])
    if messages is None:
        errors["unparsed_sendmmsg_vector"] += 1
        return [(UNKNOWN_TARGET, local, peer, None)]
    targets = []
    for message in messages:
        fields = struct_fields(message)
        header = struct_fields(fields.get("msg_hdr", "")) if fields else None
        targets.append(target(header.get("msg_name", "") if header else "", connected=True))
    if len(messages) != int(count):
        errors["incomplete_sendmmsg_vector"] += 1
        targets.append((UNKNOWN_TARGET, local, peer, None))
    return targets


def destination(args):
    """Legacy helper; parse one sockaddr or connected peer without payload scans."""
    parts = split_arguments(args)
    if parts and len(parts) in {3, 6}:
        name = "sendto" if len(parts) == 6 else "sendmsg" if parts[1].startswith("{msg_") else "connect"
        targets = call_targets(name, args, collections.Counter())
        if len(targets) == 1:
            return targets[0][0][:3]
    return UNKNOWN_TARGET[:3]


def parse_trace(lines, policy):
    """Parse trusted strace text; no namespace/process provenance is inferred.

    Optional -ttt epoch timestamps appear as event['timestamp'] (float). A
    resumed call uses its unfinished start timestamp. Without timestamps,
    identical sanitized events retain the legacy aggregation/count behavior.
    Unknown lines, incomplete calls/vectors and usable/submitted io_uring set
    parse_errors. Kernel-refused setup probes cannot create a ring or submit I/O.
    """
    pending = {}
    attempts = collections.Counter()
    errors = collections.Counter()
    total, trace_bytes = 0, 0

    def record(pid, name, args, result=None, error=None, timestamp=None):
        nonlocal total
        if name in PROCESS_CALLS:
            return
        if name == "io_uring_setup" and result == -1 and error in {"EPERM", "EACCES", "ENOSYS"}:
            # A refused capability probe created no ring and cannot submit I/O.
            # Successful setup, enter/register and ambiguous failures stay closed.
            targets = [(("KERNEL_ONLY", None, None, "refused_uring_setup"), None, None, None)]
        elif name in URING_CALLS:
            errors["unsupported_unobserved_network_path"] += 1
            targets = [(("unknown", None, None, "unsupported"), None, None, None)]
        else:
            targets = call_targets(name, args, errors)
        for (family, ip, port, kind), local, peer, transport in targets:
            if total >= MAX_ATTEMPTS:
                errors["trace_limit_exceeded"] += 1
                return
            total += 1
            basis = "denied"
            if kind == "unix":
                basis = "unix"
            elif kind == "kernel_netlink":
                basis = "kernel_netlink"
            elif kind == "disconnect" and name == "connect":
                basis = "unspec_disconnect"
            elif kind == "refused_uring_setup":
                basis = "kernel_refused_io_uring_setup"
            elif kind in {"endpoint", "connected"} and policy.allows(family, ip, port):
                basis = "exact_endpoint" if not policy.broad else "fixture_loopback"
            elif (kind == "connected" and name != "connect" and transport in {"TCP", "TCPv6"}
                  and policy.allows_reply(local, peer)):
                basis = "accepted_reply"
            if kind == "unresolved":
                errors["unresolved_destination"] += 1
            attempts[(pid, name, family, ip, port, result, error, basis != "denied", basis,
                      local[0] if local else None, local[1] if local else None, timestamp)] += 1

    def flush(pid):
        name, body, timestamp = pending.pop(pid)
        errors["incomplete_syscall"] += 1
        record(pid, name, body.partition("(")[2], timestamp=timestamp)

    for line in lines:
        if not isinstance(line, str):
            errors["unparsed_trace_line"] += 1
            continue
        trace_bytes += len(line.encode("utf-8", errors="replace"))
        if len(line) > MAX_LINE_BYTES or trace_bytes > MAX_TRACE_BYTES or total >= MAX_ATTEMPTS:
            errors["trace_limit_exceeded"] += 1
            break
        body = line.strip()
        prefix = re.match(r"(?:\[pid\s+([0-9]{1,10})\]\s*|([0-9]{1,10})\s+)(.*)", body)
        pid, body = (int(prefix[1] or prefix[2]), prefix[3]) if prefix else (0, body)
        epoch = re.match(r"([0-9]{1,12}\.[0-9]{1,9})\s+(.*)", body)
        timestamp, body = (float(epoch[1]), epoch[2]) if epoch else (None, body)
        if not body or re.fullmatch(r"\+\+\+ (?:exited with [0-9]+|killed by SIG[A-Z0-9]+) \+\+\+(?: \(core dumped\))?", body):
            continue
        if re.fullmatch(r"--- SIG[A-Z0-9]+ .* ---", body):
            continue
        resumed = re.match(r"<\.\.\. ([a-zA-Z_][a-zA-Z_0-9]*) resumed>(.*)", body)
        if resumed:
            if pid not in pending or pending[pid][0] != resumed[1]:
                errors["orphan_resumed_syscall"] += 1
                continue
            _, start, timestamp = pending.pop(pid)
            body = start + resumed[2]
        call = re.match(r"([a-zA-Z_][a-zA-Z_0-9]*)\((.*)", body)
        if not call:
            errors["unparsed_trace_line"] += 1
            continue
        name = call[1]
        if name not in NETWORK_CALLS | URING_CALLS | PROCESS_CALLS:
            errors["unsupported_syscall"] += 1
            continue
        if pid in pending:
            errors["duplicate_unfinished_syscall"] += 1
            flush(pid)  # Never overwrite and lose a prior remote attempt.
        if body.endswith("<unfinished ...>"):
            pending[pid] = name, body.removesuffix("<unfinished ...>"), timestamp
            continue
        complete = re.fullmatch(r"(.*)\)\s+=\s+(-?[0-9]{1,20}|\?)(?:\s+([A-Z][A-Z0-9_]*))?(?:\s+\(.*\))?", call[2])
        if not complete:
            errors["unparsed_syscall_result"] += 1
            # The closing syscall delimiter may remain in malformed results.
            args = call[2].rsplit(") =", 1)[0] if ") =" in call[2] else call[2]
            record(pid, name, args, timestamp=timestamp)
            continue
        result = int(complete[2]) if complete[2] != "?" else None
        error = complete[3]
        if result is None:
            errors["unknown_syscall_result"] += 1
        if error and error not in ERRNOS:
            errors["unparsed_syscall_result"] += 1
            error = None
        if name in PROCESS_CALLS:
            parts = split_arguments(complete[1])
            if (parts is None or (name in {"fork", "vfork"} and parts)
                    or (name == "clone3" and len(parts) != 2)
                    or (name == "clone" and len(parts) < 2)):
                errors["unparsed_syscall_arguments"] += 1
        record(pid, name, complete[1], result, error, timestamp)
    for pid in list(pending):
        flush(pid)
    events = []
    for key, count in attempts.items():
        event = {"pid": key[0], "syscall": key[1], "family": key[2], "ip": key[3],
                 "port": key[4], "return": key[5], "errno": key[6], "allowed": key[7],
                 "policy_basis": key[8], "local_ip": key[9], "local_port": key[10], "count": count}
        if key[11] is not None:
            event["timestamp"] = key[11]
        events.append(event)
    return {"attempts": events, "attempt_count": total,
            "denied_count": sum(event["count"] for event in events if not event["allowed"]),
            "inet_attempt_count": sum(event["count"] for event in events if event["family"] in {"AF_INET", "AF_INET6"}),
            "parse_errors": dict(errors)}


def make_report(observation, policy, returncode, failure=None):
    failures = [] if failure is None else [failure]
    if returncode != 0:
        failures.append("command_failed")
    if observation["denied_count"]:
        failures.append("unapproved_network_attempt")
    if observation["parse_errors"]:
        failures.append("incomplete_observation")
    if not observation["inet_attempt_count"]:
        failures.append("no_inet_attempts_observed")
    return {"result": "fail" if failures else "pass", "failures": failures,
            "command_returncode": returncode, "policy": policy.summary(),
            "network": ("candidate_namespace_and_trace_provenance_are_callers_responsibility" if policy.candidate else
                        "loopback_only_namespace_verified; Docker --network none required"),
            "payload_bytes_recorded": 0, "limits": LIMITS, **observation}


def observe(command, *, timeout, fixture_ports=None, broad=False):
    if not loopback_namespace():
        raise ObservationError("network_none_namespace_required")
    if not shutil.which("strace"):
        raise ObservationError("strace_missing")
    if not command or bool(fixture_ports) == bool(broad):
        raise ObservationError("exactly_one_fixture_policy_required")
    with tempfile.TemporaryDirectory(prefix="xiaozhi-egress-") as temporary:
        root = Path(temporary)
        trace = root / "network.trace"
        failure = None
        # No shell, child payload logs, execve argv capture or inherited secrets.
        process = subprocess.Popen(trace_argv(command, trace), env=clean_environment(root),
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    failure = "command_timeout"
                    break
                if trace.exists() and trace.stat().st_size > MAX_TRACE_BYTES:
                    failure = "trace_limit_exceeded"
                    break
                time.sleep(0.025)
        finally:
            if process.poll() is None:
                stop_tracees(process)
            process.wait(timeout=5)
        policy = Policy(broad=True) if broad else load_policy(fixture_ports)
        if not trace.is_file():
            raise ObservationError("trace_not_created")
        if trace.stat().st_size > MAX_TRACE_BYTES:
            failure = "trace_limit_exceeded"
        with trace.open(encoding="utf-8", errors="replace") as stream:
            observation = parse_trace(iter(lambda: stream.readline(MAX_LINE_BYTES + 1), ""), policy)
        return make_report(observation, policy, process.returncode, failure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--network-none", required=True, action="store_true",
                        help="acknowledge the required Docker --network none runner")
    policies = parser.add_mutually_exclusive_group(required=True)
    policies.add_argument("--fixture-ports", type=Path, help="exact endpoint JSON, read after the fixture exits")
    policies.add_argument("--fixture-loopback-only", action="store_true", help="explicit ANY non-DNS-port fallback on 127.0.0.1/::1")
    parser.add_argument("--timeout", type=int, choices=range(1, 301), default=90, metavar="1..300")
    parser.add_argument("--report", type=Path, help="optional sanitized JSON report; raw trace is always deleted")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- command [args...]")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        report = observe(command, timeout=args.timeout, fixture_ports=args.fixture_ports,
                         broad=args.fixture_loopback_only)
    except (ObservationError, OSError, ValueError, subprocess.SubprocessError) as error:
        report = {"result": "fail", "failure": str(error) if isinstance(error, ObservationError)
                  else "observer_setup_failed", "limits": LIMITS}
    output = json.dumps(report, sort_keys=True)
    if args.report:
        try:
            args.report.write_text(output + "\n", encoding="utf-8")
        except OSError:
            print(json.dumps({"result": "fail", "failure": "report_write_failed"}))
            return 1
    print(output)
    return int(report["result"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
