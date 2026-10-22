#!/usr/bin/env python3
"""Aggregate candidate-only syscall, DNS, firewall and scenario metadata.

Raw traces stay inside the synthetic audit volume and are deleted at teardown.
This report is a bounded runtime witness, not adversarial containment or a
statement about providers/scenarios that were not exercised.
"""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time

SPEC = importlib.util.spec_from_file_location("egress", Path(__file__).with_name("service-egress-check.py"))
egress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(egress)
PHASES = ("startup", "account-binding-config-history", "websocket-turn", "mqtt-udp-turn",
          "summary-history", "removed-features", "shutdown", "finish")
PORTS = (53, 8000, 8002, 8003, 8005, 8007, 18883, 18884, 19200)
LABEL = "service-policy-rehearsal-20261021"


def load(path, limit=262144):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise ValueError("invalid_metadata_file")
    return json.loads(path.read_text())


def policy_for(root, *, client_port=True):
    mapping = load(root / "mapping.json")
    if set(mapping) != {"candidate-db", "candidate-redis"}:
        raise ValueError("invalid_fixture_mapping")
    endpoints = [(ip, port) for ip in ("127.0.0.1", "::1") for port in PORTS]
    endpoints += [(mapping["candidate-db"], 3306), (mapping["candidate-redis"], 6379)]
    if client_port:
        client = load(root / "mqtt-client-port.json")
        if (set(client) != {"ip", "port", "protocol", "role"} or client["ip"] != "127.0.0.1"
                or client["protocol"] != "udp" or client["role"] != "mqtt-client"
                or type(client["port"]) is not int or not 1024 <= client["port"] <= 65535):
            raise ValueError("invalid_client_port_manifest")
        endpoints.append((client["ip"], client["port"]))
    return egress.Policy(endpoints, candidate=True,
                         local_endpoints=[(ip, port) for ip in ("127.0.0.1", "::1") for port in PORTS],
                         reply_peer_ips=("127.0.0.1", "::1"))


def parse_file(path, policy):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > egress.MAX_TRACE_BYTES:
        raise ValueError("invalid_trace_file")
    with path.open() as stream:
        return egress.parse_trace(iter(lambda: stream.readline(egress.MAX_LINE_BYTES + 1), ""), policy)


def firewall_counts():
    counts = {}
    for binary in ("iptables", "ip6tables"):
        result = subprocess.run([binary, "-w", "5", "-nvxL", "XZPOLICY_OUT"], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        drops = re.findall(r"^\s*(\d+)\s+\d+\s+DROP\s", result.stdout, re.M)
        if len(drops) != 1:
            raise ValueError("invalid_firewall_witness")
        counts[binary] = int(drops[0])
    return counts


def negative_report(root):
    observed = parse_file(root / "negative.trace", policy_for(root, client_port=False))
    dns = load(root / "dns.json")
    drops = firewall_counts()
    detected = (observed["denied_count"] >= 2 and not observed["parse_errors"]
                and dns["result"] == "fail" and sum(drops.values()) >= 2)
    return {"kind": "candidate-egress-negative-controls", "result": "pass" if detected else "fail",
            "unknown_numeric_attempts_detected": observed["denied_count"],
            "unknown_dns_questions_detected": sum(dns["rejected_question_hashes"].values()),
            "firewall_drop_packets": drops, "parse_errors": observed["parse_errors"],
            "payload_bytes_recorded": 0}


def build_report(root):
    phases = load(root / "phases.json", 65536)
    if ([phase.get("name") for phase in phases] != list(PHASES) or
            any(type(phase.get("start")) not in (int, float) for phase in phases) or
            any(a["start"] >= b["start"] for a, b in zip(phases, phases[1:]))):
        raise ValueError("invalid_phase_metadata")
    def phase_for(stamp):
        matches = [item["name"] for item in phases if stamp >= item["start"]]
        return matches[-1] if matches else "before_startup"
    policy = policy_for(root)
    failures, roles = [], {}
    counts = collections.Counter()
    for role in ("manager", "voice", "gateway", "removed-features"):
        observed = parse_file(root / f"{role}.trace", policy)
        roles[role] = {key: observed[key] for key in
                       ("attempt_count", "inet_attempt_count", "denied_count", "parse_errors")}
        if observed["denied_count"] or observed["parse_errors"] or not observed["inet_attempt_count"]:
            failures.append(role + "_observation_failed")
        for event in observed["attempts"]:
            if "timestamp" not in event:
                failures.append(role + "_missing_timestamp")
                continue
            phase = phase_for(event["timestamp"])
            counts[(phase, role, event["syscall"], event["family"], event["ip"], event["port"],
                    event["allowed"])] += event["count"]
    dns = load(root / "dns.json")
    if dns["result"] != "pass" or not dns["allowed_questions"] or dns["forwarded_requests"]:
        failures.append("dns_observation_failed")
    dns_by_phase = collections.Counter((phase_for(e["timestamp"]), e["question"], e["type"], e["allowed"])
                                       for e in dns["events"])
    drops = firewall_counts()
    if sum(drops.values()):
        failures.append("firewall_blocked_unexpected_attempt")
    controls = load(root / "negative-controls.json")
    if controls.get("result") != "pass":
        failures.append("negative_controls_failed")
    scenarios = load(root / "scenarios.json")
    if set(scenarios) != {"api", "websocket", "mqtt_udp", "summary_history", "removed_features"} or not all(
            value.get("result") == "pass" for value in scenarios.values()):
        failures.append("scenario_failed_or_missing")
    return {"kind": "full-candidate-dns-egress-observation", "fixture": LABEL,
            "result": "fail" if failures else "pass", "failures": sorted(set(failures)),
            "roles": roles, "phase_names": list(PHASES), "scenarios": scenarios,
            "dns": {key: value for key, value in dns.items() if key != "events"},
            "dns_by_phase": [{"phase": k[0], "question": k[1], "type": k[2], "allowed": k[3], "count": v}
                             for k, v in dns_by_phase.items()],
            "observed_attempts": [{"phase": k[0], "role": k[1], "syscall": k[2], "family": k[3],
                                   "ip": k[4], "port": k[5], "allowed": k[6], "count": v}
                                  for k, v in counts.items()],
            "firewall_drop_packets": drops, "negative_controls": controls,
            "policy": policy.summary(), "payload_bytes_recorded": 0,
            "limits": ["Only the explicitly exercised synthetic scenarios, not real AI quality.",
                       "Not adversarial containment; no privileged/unconfined or host-PID access.",
                       "Application execs and ordinary descendants traced from startup; infrastructure DNS/firewall are trusted fixtures.",
                       "DNS names witnessed by the nonforwarding local resolver; other destinations and unsupported io_uring fail closed."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("phase", "negative", "report"))
    parser.add_argument("name", nargs="?", choices=PHASES)
    args = parser.parse_args()
    if os.environ.get("CANDIDATE_EGRESS_FIXTURE") != LABEL:
        raise SystemExit("candidate_fixture_required")
    root = Path("/audit-out")
    try:
        if args.command == "phase":
            previous = load(root / "phases.json") if (root / "phases.json").exists() else []
            if args.name != PHASES[len(previous)]:
                raise ValueError("phase_order_mismatch")
            previous.append({"name": args.name, "start": time.time()})
            (root / "phases.json").write_text(json.dumps(previous))
            print(json.dumps({"phase": args.name}))
            return
        result = negative_report(root) if args.command == "negative" else build_report(root)
        if args.command == "negative":
            (root / "negative-controls.json").write_text(json.dumps(result))
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(int(result["result"] != "pass"))
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError):
        raise SystemExit("candidate_network_report_failed") from None


if __name__ == "__main__":
    main()
