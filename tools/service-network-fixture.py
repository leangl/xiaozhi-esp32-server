#!/usr/bin/env python3
"""Candidate-only DNS witness and namespace firewall; never an upstream resolver.

Run only inside the labelled disposable candidate's shared network namespace.
No packet/conversation bodies, query text, URLs or credentials enter reports.
Unknown DNS names are represented by SHA256, never printed. The resolver has
no forwarding path. Main must separately observe app syscalls from startup.
"""
import argparse
import collections
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import socketserver
import struct
import subprocess
import threading
import time

LABEL = "service-policy-rehearsal-20261021"
TCP_PORTS = (53, 8000, 8002, 8003, 8005, 8007, 18883, 19200)
UDP_PORTS = (53, 18884)


def fixture_mapping(path):
    data = json.loads(Path(path).read_text())
    if set(data) != {"candidate-db", "candidate-redis"}:
        raise ValueError("invalid_fixture_mapping")
    for value in data.values():
        ip = ipaddress.ip_address(value)
        if ip.version != 4 or not ip.is_private or ip.is_loopback or ip.is_unspecified:
            raise ValueError("invalid_fixture_mapping")
    if len(set(data.values())) != 2:
        raise ValueError("invalid_fixture_mapping")
    return data


def question(packet):
    if not 12 <= len(packet) <= 4096:
        raise ValueError("invalid_dns_packet")
    ident, flags, count, answers, authority, _additional = struct.unpack("!6H", packet[:12])
    if flags & 0x8000 or flags & 0x7800 or count != 1 or answers or authority:
        raise ValueError("invalid_dns_packet")
    position, labels = 12, []
    while True:
        if position >= len(packet):
            raise ValueError("invalid_dns_question")
        length = packet[position]
        position += 1
        if length == 0:
            break
        # Queries must have an uncompressed, bounded, ASCII hostname.
        if length > 63 or position + length > len(packet):
            raise ValueError("invalid_dns_question")
        label = packet[position:position + length].decode("ascii").lower()
        if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in label):
            raise ValueError("invalid_dns_question")
        labels.append(label)
        position += length
    if not labels or position + 4 > len(packet) or position > 267:
        raise ValueError("invalid_dns_question")
    qtype, qclass = struct.unpack("!HH", packet[position:position + 4])
    if qclass != 1:
        raise ValueError("invalid_dns_class")
    return ident, ".".join(labels), qtype, packet[12:position + 4]


class DNSWitness:
    def __init__(self, mapping, output=None):
        self.mapping = dict(mapping, localhost="127.0.0.1")
        self.output = Path(output) if output else None
        self.lock = threading.Lock()
        self.counts = collections.Counter()
        self.allowed = collections.Counter()
        self.rejected = collections.Counter()
        self.events = []

    def snapshot(self):
        return {"kind": "candidate-dns-witness", "result": "fail" if
                self.rejected or self.counts["malformed"] else "pass",
                "counts": dict(self.counts), "allowed_questions": dict(self.allowed),
                "rejected_question_hashes": dict(self.rejected), "forwarded_requests": 0,
                "events": list(self.events),
                "payload_bytes_recorded": 0}

    def save(self):
        if self.output:
            temporary = self.output.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.snapshot(), sort_keys=True) + "\n")
            temporary.replace(self.output)

    def answer(self, packet, transport):
        with self.lock:
            self.counts[transport] += 1
            try:
                ident, name, qtype, wire_question = question(packet)
                permitted = name in self.mapping and qtype in (1, 28)
                if permitted:
                    self.allowed[f"{name}/{qtype}"] += 1
                else:
                    digest = hashlib.sha256((name + "/" + str(qtype)).encode()).hexdigest()
                    self.rejected[digest] += 1
                if len(self.events) >= 1000:
                    raise ValueError("dns_observation_limit")
                self.events.append({"timestamp": time.time(), "question": name if permitted else None,
                                    "question_hash": None if permitted else digest, "type": qtype,
                                    "transport": transport, "allowed": permitted})
                address = self.mapping.get(name) if qtype == 1 else "::1" if name == "localhost" else None
                data = ipaddress.ip_address(address).packed if permitted and address else b""
                answer = (b"\xc0\x0c" + struct.pack("!HHIH", qtype, 1, 0, len(data)) + data) if data else b""
                reply = struct.pack("!6H", ident, 0x8180 if permitted else 0x8183,
                                    1, int(bool(answer)), 0, 0) + wire_question + answer
            except (ValueError, UnicodeError, struct.error):
                self.counts["malformed"] += 1
                reply = b""
            self.save()
            return reply


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        packet, connection = self.request
        reply = self.server.witness.answer(packet, "udp")
        if reply:
            connection.sendto(reply, self.client_address)


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        try:
            length = self.read_exact(2)
            packet = self.read_exact(struct.unpack("!H", length)[0])
            reply = self.server.witness.answer(packet, "tcp")
            if reply:
                self.request.sendall(struct.pack("!H", len(reply)) + reply)
        except (OSError, ValueError, struct.error):
            with self.server.witness.lock:
                self.server.witness.counts["malformed"] += 1
                self.server.witness.save()

    def read_exact(self, size):
        if size > 4096:
            raise ValueError()
        result = b""
        while len(result) < size:
            chunk = self.request.recv(size - len(result))
            if not chunk:
                raise ValueError()
            result += chunk
        return result


def firewall_plan(mapping, binary="iptables"):
    if binary not in {"iptables", "ip6tables"}:
        raise ValueError("invalid_firewall_tool")
    loopback = "127.0.0.1" if binary == "iptables" else "::1"
    base = [binary, "-w", "5"]
    commands = [base + ["-N", "XZPOLICY_OUT"], base + ["-I", "OUTPUT", "1", "-j", "XZPOLICY_OUT"],
                base + ["-A", "XZPOLICY_OUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"]]
    for protocol, ports in (("tcp", TCP_PORTS), ("udp", UDP_PORTS)):
        commands.append(base + ["-A", "XZPOLICY_OUT", "-d", loopback, "-p", protocol,
                               "-m", "multiport", "--dports", ",".join(map(str, ports)), "-j", "ACCEPT"])
    if binary == "iptables":
        for name, port in (("candidate-db", 3306), ("candidate-redis", 6379)):
            commands.append(base + ["-A", "XZPOLICY_OUT", "-d", mapping[name], "-p", "tcp",
                                   "--dport", str(port), "-j", "ACCEPT"])
    commands.append(base + ["-A", "XZPOLICY_OUT", "-j", "DROP"])
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dns", "firewall"))
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--output")
    parser.add_argument("--candidate-only", required=True, action="store_true")
    args = parser.parse_args()
    if os.environ.get("CANDIDATE_EGRESS_FIXTURE") != LABEL:
        raise SystemExit("candidate_fixture_required")
    try:
        mapping = fixture_mapping(args.mapping)
        if args.command == "firewall":
            for binary in ("iptables", "ip6tables"):
                for command in firewall_plan(mapping, binary):
                    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(json.dumps({"fixture": LABEL, "firewall": "exact-targets-default-drop"}), flush=True)
            return
        if not args.output:
            raise ValueError()
        witness = DNSWitness(mapping, args.output)
        servers = [socketserver.ThreadingUDPServer(("127.0.0.1", 53), UDPHandler),
                   socketserver.ThreadingTCPServer(("127.0.0.1", 53), TCPHandler)]
        for server in servers:
            server.witness = witness
            server.daemon_threads = True
            threading.Thread(target=server.serve_forever, daemon=True).start()
        witness.save()
        print(json.dumps({"fixture": LABEL, "dns_ready": True}), flush=True)
        done = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: done.set())
        signal.signal(signal.SIGINT, lambda *_: done.set())
        done.wait()
        for server in servers:
            server.shutdown()
            server.server_close()
        with witness.lock:
            witness.save()
        print(json.dumps(witness.snapshot()), flush=True)
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit("candidate_network_fixture_failed") from None


if __name__ == "__main__":
    main()
