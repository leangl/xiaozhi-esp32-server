#!/usr/bin/env python3
"""Offline DNS witness and namespace firewall-plan contract tests."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("fixture", Path(__file__).with_name("service-network-fixture.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def query(name, qtype=1):
    return struct.pack("!6H", 123, 0x100, 1, 0, 0, 0) + b"".join(
        bytes([len(label)]) + label.encode() for label in name.split(".")) + b"\0" + struct.pack("!HH", qtype, 1)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {"candidate-db": "172.30.0.2", "candidate-redis": "172.30.0.3"}
        self.witness = fixture.DNSWitness(self.mapping)

    def test_allowed_a_and_empty_aaaa(self):
        a = self.witness.answer(query("candidate-db"), "udp")
        self.assertEqual(struct.unpack("!6H", a[:12])[3], 1)
        self.assertTrue(a.endswith(bytes([172, 30, 0, 2])))
        aaaa = self.witness.answer(query("candidate-db", 28), "tcp")
        self.assertEqual(struct.unpack("!6H", aaaa[:12])[3], 0)
        self.assertEqual(self.witness.snapshot()["result"], "pass")
        self.assertEqual(self.witness.snapshot()["forwarded_requests"], 0)

    def test_unknown_hostname_is_denied_and_redacted(self):
        secret = "synthetic-secret-token.invalid"
        response = self.witness.answer(query(secret), "udp")
        self.assertEqual(struct.unpack("!6H", response[:12])[1] & 15, 3)
        report = json.dumps(self.witness.snapshot())
        self.assertNotIn(secret, report)
        self.assertNotIn("synthetic-secret", report)
        self.assertEqual(self.witness.snapshot()["result"], "fail")
        self.assertEqual(sum(self.witness.rejected.values()), 1)

    def test_case_normalization_and_localhost(self):
        self.witness.answer(query("Candidate-DB"), "udp")
        self.witness.answer(query("localhost", 28), "udp")
        self.assertEqual(self.witness.allowed["candidate-db/1"], 1)
        self.assertEqual(self.witness.snapshot()["result"], "pass")

    def test_bad_dns_packets_fail_closed(self):
        packets = [b"", b"x" * 4097, struct.pack("!6H", 1, 0x100, 1, 0, 0, 0) + b"\xc0\x0c",
                   query("candidate-db")[:15], query("candidate-db").replace(b"\x00\x01\x00\x01", b"\x00\x01\x00\x03")]
        for packet in packets:
            with self.subTest(size=len(packet)):
                self.assertEqual(self.witness.answer(packet, "udp"), b"")
        self.assertEqual(self.witness.counts["malformed"], len(packets))

    def test_snapshot_contains_only_fixed_names_and_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dns.json"
            witness = fixture.DNSWitness(self.mapping, path)
            witness.answer(query("candidate-db"), "udp")
            self.assertEqual(json.loads(path.read_text())["allowed_questions"], {"candidate-db/1": 1})

    def test_mapping_requires_exact_candidate_services(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "mapping.json"
            for mapping in ({"real-db": "172.30.0.2"}, dict(self.mapping, extra="172.30.0.5"),
                            dict(self.mapping, **{"candidate-db": "8.8.8.8"}),
                            dict(self.mapping, **{"candidate-db": "127.0.0.1"}),
                            dict(self.mapping, **{"candidate-db": "172.30.0.3"})):
                path.write_text(json.dumps(mapping))
                with self.assertRaises(ValueError):
                    fixture.fixture_mapping(path)
            path.write_text(json.dumps(self.mapping))
            self.assertEqual(fixture.fixture_mapping(path), self.mapping)

    def test_firewall_is_default_drop_with_exact_services(self):
        for binary in ("iptables", "ip6tables"):
            plan = fixture.firewall_plan(self.mapping, binary)
            self.assertEqual(plan[-1][-1], "DROP")
            self.assertTrue(all(command[0] == binary for command in plan))
            text = json.dumps(plan)
            self.assertNotIn("0.0.0.0/0", text)
            self.assertNotIn("::/0", text)
            self.assertIn("ESTABLISHED,RELATED", text)
            self.assertIn("--dports", text)
        v4 = json.dumps(fixture.firewall_plan(self.mapping))
        self.assertIn("172.30.0.2", v4)
        self.assertIn("3306", v4)
        self.assertIn("6379", v4)


if __name__ == "__main__":
    unittest.main()
