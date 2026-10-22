#!/usr/bin/env python3
"""Exercise retained rejection/context code in the observed synthetic voice image."""
import asyncio
import collections
import copy
import json
import logging
import os
import sys
from types import SimpleNamespace


def run():
    if os.environ.get("CANDIDATE_EGRESS_FIXTURE") != "service-policy-rehearsal-20261021":
        raise ValueError()
    sys.path.insert(0, os.getcwd())
    from config.config_loader import load_config
    config = asyncio.run(load_config())
    from config.logger import setup_logging
    logger = setup_logging(config)
    logger.remove()
    logging.disable(logging.CRITICAL)
    from config.provider_profile import ProviderProfileError, validate_config
    from config.service_policy import ServicePolicyError, validate_endpoint
    from core.providers.tools.unified_tool_manager import ToolManager
    from core.utils.util import get_ip_info
    from plugins_func.unavailable import REMOVED_TOOLS
    counts = collections.Counter()
    for capability in ("asr", "llm", "tts", "context", "tool", "mcp", "memory", "voiceprint"):
        try:
            validate_endpoint("https://unreviewed.invalid/fixture", capability)
        except ServicePolicyError:
            counts["unapproved_endpoint_rejected"] += 1
        else:
            raise ValueError()
    removed = copy.deepcopy(config)
    selected = removed["selected_module"]["ASR"]
    removed["ASR"][selected]["type"] = "fun_local"
    try:
        validate_config(removed, partial=True)
    except ProviderProfileError:
        counts["removed_provider_rejected"] += 1
    else:
        raise ValueError()
    manager = ToolManager(SimpleNamespace())
    for name in sorted(REMOVED_TOOLS):
        if manager.has_tool(name) or asyncio.run(manager.execute_tool(name, {"query": "synthetic"})).result != "service_unavailable":
            raise ValueError()
        counts["stale_tool_rejected"] += 1
    if get_ip_info("203.0.113.17", logger) != {}:
        raise ValueError()
    counts["location_lookup_unavailable"] += 1
    return {"result": "pass", "scope": "candidate-removed-feature-paths", "counts": dict(counts)}


if __name__ == "__main__":
    try:
        result = run()
    except Exception:
        result = {"result": "fail", "failure": "removed_feature_fixture_failed"}
    print(json.dumps(result))
    raise SystemExit(int(result["result"] != "pass"))
