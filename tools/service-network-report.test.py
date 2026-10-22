#!/usr/bin/env python3
"""Offline aggregation gates, with no Docker or system firewall access."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("report", Path(__file__).with_name("service-network-report.py"))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.write("mapping.json", {"candidate-db": "172.30.0.2", "candidate-redis": "172.30.0.3"})
        self.write("mqtt-client-port.json", {"ip": "127.0.0.1", "port": 32001, "protocol": "udp", "role": "mqtt-client"})
        self.write("phases.json", [{"name": name, "start": index + 1} for index, name in enumerate(report.PHASES)])
        self.write("dns.json", {"result": "pass", "allowed_questions": {"candidate-db/1": 1},
                               "rejected_question_hashes": {}, "forwarded_requests": 0,
                               "events": [{"timestamp": 1.1, "question": "candidate-db", "type": 1, "allowed": True}]})
        self.write("negative-controls.json", {"result": "pass"})
        self.write("scenarios.json", {key: {"result": "pass"} for key in
                                      ("api", "websocket", "mqtt_udp", "summary_history", "removed_features")})
        for role in ("manager", "voice", "gateway", "removed-features"):
            (self.root / (role + ".trace")).write_text('1 1.200000 connect(3, {sa_family=AF_INET, '
                'sin_port=htons(8002), sin_addr=inet_addr("127.0.0.1")}, 16) = 0\n')
        self.firewall = patch.object(report, "firewall_counts", return_value={"iptables": 0, "ip6tables": 0})
        self.firewall.start()

    def tearDown(self):
        self.firewall.stop()
        self.temporary.cleanup()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def test_complete_exact_metadata_passes_and_groups_by_role_phase(self):
        value = report.build_report(self.root)
        self.assertEqual(value["result"], "pass")
        self.assertEqual(len(value["roles"]), 4)
        self.assertTrue(all(row["phase"] == "startup" for row in value["observed_attempts"]))
        self.assertEqual(value["dns_by_phase"][0]["question"], "candidate-db")

    def test_unknown_attempt_fails_even_when_kernel_rejects_it(self):
        (self.root / "gateway.trace").write_text('1 4.100000 connect(3, {sa_family=AF_INET, '
            'sin_port=htons(443), sin_addr=inet_addr("198.51.100.1")}, 16) = -1 ENETUNREACH (unreachable)\n')
        value = report.build_report(self.root)
        self.assertEqual(value["result"], "fail")
        self.assertEqual(value["roles"]["gateway"]["denied_count"], 1)
        self.assertEqual(value["observed_attempts"][2]["phase"], "mqtt-udp-turn")

    def test_missing_scenario_or_failed_dns_or_firewall_never_passes(self):
        scenarios = json.loads((self.root / "scenarios.json").read_text())
        dns = json.loads((self.root / "dns.json").read_text())
        for field in ("scenario", "dns", "firewall"):
            with self.subTest(field=field):
                self.write("scenarios.json", scenarios)
                self.write("dns.json", dns)
                if field == "scenario":
                    self.write("scenarios.json", {})
                elif field == "dns":
                    self.write("dns.json", {"result": "fail", "allowed_questions": {}, "forwarded_requests": 0, "events": []})
                with patch.object(report, "firewall_counts", return_value={"iptables": int(field == "firewall"), "ip6tables": 0}):
                    result = report.build_report(self.root)
                    self.assertEqual(result["result"], "fail")
                    expected = {"scenario": "scenario_failed_or_missing", "dns": "dns_observation_failed",
                                "firewall": "firewall_blocked_unexpected_attempt"}[field]
                    self.assertIn(expected, result["failures"])

    def test_malformed_and_missing_traces_fail_closed_without_echo(self):
        secret = "DO_NOT_ECHO_SYNTHETIC_SECRET"
        (self.root / "manager.trace").write_text(secret + "\n")
        value = report.build_report(self.root)
        self.assertEqual(value["result"], "fail")
        self.assertNotIn(secret, json.dumps(value))
        (self.root / "manager.trace").unlink()
        with self.assertRaises(ValueError):
            report.build_report(self.root)

    def test_no_wildcard_client_manifest(self):
        self.write("mqtt-client-port.json", {"ip": "0.0.0.0", "port": 32001, "protocol": "udp", "role": "mqtt-client"})
        with self.assertRaises(ValueError):
            report.policy_for(self.root)

    def test_missing_timestamp_or_phase_does_not_pass(self):
        (self.root / "manager.trace").write_text('1 connect(3, {sa_family=AF_INET, '
            'sin_port=htons(8002), sin_addr=inet_addr("127.0.0.1")}, 16) = 0\n')
        self.assertEqual(report.build_report(self.root)["result"], "fail")
        self.write("phases.json", [])
        with self.assertRaises(ValueError):
            report.build_report(self.root)


if __name__ == "__main__":
    unittest.main()
