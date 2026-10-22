"""IP context removal must not send device addresses or resurrect cached data."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.utils.prompt_manager import PromptManager
from core.utils.util import get_ip_info


@pytest.mark.parametrize("address", ["8.8.8.8", "192.168.2.3", "::1", "", None])
def test_legacy_ip_lookup_is_inert(address, monkeypatch):
    import requests

    monkeypatch.setattr(requests, "get", Mock(side_effect=AssertionError("No HTTP lookup")))
    assert get_ip_info(address, Mock()) == {}
    requests.get.assert_not_called()


def manager():
    instance = PromptManager.__new__(PromptManager)
    instance.logger = Mock()
    instance.cache_manager = Mock()
    instance.cache_manager.get.side_effect = AssertionError("Do not read retired context cache")
    instance.CacheType = SimpleNamespace(DEVICE_PROMPT="device")
    instance.config = {}
    instance.base_prompt_template = "{{base_prompt}}|{{local_address}}|{{weather_info}}"
    instance.context_data = ""
    instance.context_provider = Mock()
    instance._get_current_time_info = Mock(return_value=("date", "day", ""))
    return instance


def test_prompt_does_not_reuse_retired_location_or_weather():
    instance = manager()
    assert instance.build_enhanced_prompt("Question", "fixture-device", "8.8.8.8") == "Question||"
    instance.cache_manager.get.assert_not_called()


def test_connection_context_does_not_schedule_a_weather_lookup():
    instance = manager()
    instance._get_weather_info = Mock(side_effect=AssertionError("No automatic weather"))
    instance.update_context_info(SimpleNamespace(device_id="fixture-device"), "8.8.8.8")
    instance._get_weather_info.assert_not_called()
    instance.context_provider.fetch_all.assert_not_called()
    assert instance._get_location_info("8.8.8.8") == ""
