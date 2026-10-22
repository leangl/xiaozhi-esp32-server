"""Device-owned turn boundaries: no model, credentials, or external requests."""
import asyncio
import copy
import importlib
import queue
import socket
import sys
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from config.provider_profile import ProviderProfileError, validate_provider_config
from core.providers.asr.dto.dto import InterfaceType
from core.utils import vad
from core.handle.receiveAudioHandle import handleAudioMessage
from core.handle.textHandler.listenMessageHandler import ListenTextMessageHandler
from core.providers.asr.base import ASRProviderBase
from core.connection import ConnectionHandler


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Device VAD test attempted network access")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def connection(provider):
    conn = SimpleNamespace(
        vad=provider, client_listen_mode="auto", asr_audio=[],
        client_have_voice=False, client_voice_stop=False,
        client_is_speaking=False, client_aec=False, just_woken_up=False,
        last_activity_time=0, close_after_chat=False, config={},
        logger=Mock(), close=AsyncMock(), asr_audio_queue=queue.Queue(),
        stop_event=threading.Event(),
    )
    def reset():
        conn.asr_audio.clear()
        conn.client_have_voice = False
        conn.client_voice_stop = False
    conn.reset_audio_states = Mock(side_effect=reset)
    return conn


def test_device_factory_needs_no_model_or_inference_runtime(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    monkeypatch.setitem(sys.modules, "core.providers.vad.silero", None)
    config = {"type": "device"}
    before = copy.deepcopy(config)
    validate_provider_config("VAD", config, require_ready=True)
    provider = vad.create_instance("device", config)
    assert provider.device_controlled is True
    assert config == before


@pytest.mark.parametrize("value", [1000, 60000, 300000, "120000"])
def test_device_duration_accepts_ui_integer_strings(value):
    validate_provider_config("VAD", {"type": "device", "max_audio_duration_ms": value}, require_ready=True)


@pytest.mark.parametrize("value", [None, True, False, 0, 999, 300001, 1000.5, "1000.0", "secret-path", {}, []])
def test_device_duration_rejects_invalid_values_without_echo(value):
    with pytest.raises(ProviderProfileError) as error:
        validate_provider_config("VAD", {"type": "device", "max_audio_duration_ms": value}, require_ready=True)
    assert "secret-path" not in str(error.value)


@pytest.mark.asyncio
async def test_device_turn_waits_for_stop_and_drops_audio_outside_turn():
    provider = vad.create_instance("device", {"type": "device"})
    conn = connection(provider)
    conn.asr = SimpleNamespace(
        interface_type=InterfaceType.NON_STREAM,
        receive_audio=AsyncMock(side_effect=lambda c, pcm, voice: c.asr_audio.append(pcm)),
        drain_audio_queue=AsyncMock(), handle_voice_stop=AsyncMock(),
    )
    handler = ListenTextMessageHandler()
    await handleAudioMessage(conn, b"before")
    conn.asr.receive_audio.assert_not_called()
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    await handleAudioMessage(conn, b"\0\1" * 1600)
    await handleAudioMessage(conn, b"\0\0" * 1600)  # Silence cannot end a device-owned turn.
    conn.asr.handle_voice_stop.assert_not_called()
    assert len(conn.asr_audio) == 2
    # Duplicate start must not erase the question already received.
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    assert len(conn.asr_audio) == 2
    await handler.handle(conn, {"state": "stop"})
    conn.asr.drain_audio_queue.assert_awaited_once_with(conn)
    conn.asr.handle_voice_stop.assert_awaited_once_with(conn, [b"\0\1" * 1600, b"\0\0" * 1600])
    assert conn.asr_audio == []
    await handler.handle(conn, {"state": "stop"})
    await handleAudioMessage(conn, b"after")
    assert conn.asr.handle_voice_stop.await_count == 1
    assert conn.asr.receive_audio.await_count == 2
    conn.close.assert_not_called()
    # The next turn is independent; one instance can serve multiple connections.
    second = connection(provider)
    assert not provider.is_vad(second, b"\0\0")
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    await handleAudioMessage(conn, b"\1\0")
    await handler.handle(conn, {"state": "stop"})
    assert conn.asr.handle_voice_stop.await_count == 2


@pytest.mark.parametrize("mode", ["auto", "realtime", "unknown", None])
@pytest.mark.asyncio
async def test_device_mode_rejects_non_manual_start(mode):
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = Mock()
    await ListenTextMessageHandler().handle(conn, {"state": "start", "mode": mode})
    conn.close.assert_awaited_once()
    assert not conn.vad.is_vad(conn, b"\0\0")


@pytest.mark.asyncio
async def test_empty_stop_does_not_transcribe_and_late_stop_is_ignored():
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = SimpleNamespace(interface_type=InterfaceType.NON_STREAM,
                               drain_audio_queue=AsyncMock(), handle_voice_stop=AsyncMock())
    handler = ListenTextMessageHandler()
    await handler.handle(conn, {"state": "stop"})
    conn.asr.drain_audio_queue.assert_not_called()
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    await handler.handle(conn, {"state": "stop"})
    conn.asr.handle_voice_stop.assert_not_called()


@pytest.mark.parametrize("limit", ["audio", "clock"])
@pytest.mark.asyncio
async def test_missing_stop_cannot_accumulate_unbounded_audio(limit, monkeypatch):
    module = importlib.import_module("core.providers.vad.device")
    clock = [10.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    conn = connection(vad.create_instance("device", {"type": "device", "max_audio_duration_ms": 1000}))
    conn.asr = SimpleNamespace(receive_audio=AsyncMock(side_effect=lambda c, pcm, voice: c.asr_audio.append(pcm)))
    await ListenTextMessageHandler().handle(conn, {"state": "start", "mode": "manual"})
    await handleAudioMessage(conn, b"\0\0" * 8000)
    if limit == "clock":
        clock[0] += 1.1
        frame = b"\0\0"
    else:
        frame = b"\0\0" * 16000
    await handleAudioMessage(conn, frame)
    conn.close.assert_awaited_once()
    assert conn.asr_audio == []
    assert conn.asr.receive_audio.await_count == 1


@pytest.mark.asyncio
async def test_stop_queue_failure_closes_without_partial_transcription():
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = SimpleNamespace(drain_audio_queue=AsyncMock(side_effect=asyncio.TimeoutError),
                               handle_voice_stop=AsyncMock())
    handler = ListenTextMessageHandler()
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    conn.asr_audio.append(b"\0\0")
    await handler.handle(conn, {"state": "stop"})
    conn.close.assert_awaited_once()
    conn.asr.handle_voice_stop.assert_not_called()
    assert conn.asr_audio == []


@pytest.mark.asyncio
async def test_real_audio_worker_drains_queued_pcm_before_stop(monkeypatch):
    class ASR(ASRProviderBase):
        interface_type = InterfaceType.NON_STREAM
        async def speech_to_text(self, *args, **kwargs):
            return "", None
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.loop = asyncio.get_running_loop()
    conn.asr = ASR()
    conn.asr.handle_voice_stop = AsyncMock()
    handler = ListenTextMessageHandler()
    await conn.asr.open_audio_channels(conn)
    try:
        await handler.handle(conn, {"state": "start", "mode": "manual"})
        frames = [b"\0\1" * 960 for _ in range(20)]
        for pcm in frames:
            conn.asr_audio_queue.put(conn.vad.queue_audio(conn, pcm))
        # Deliberately do not yield before stop: reproduces the control/audio race.
        await handler.handle(conn, {"state": "stop"})
        conn.asr.handle_voice_stop.assert_awaited_once_with(conn, frames)
    finally:
        conn.stop_event.set()
        await asyncio.to_thread(conn.asr_priority_thread.join, 2)


def test_vad_update_detects_same_type_different_instance_and_settings():
    from core.utils.util import check_vad_update
    old = {"selected_module": {"VAD": "first"}, "VAD": {"first": {"type": "device", "max_audio_duration_ms": 60000}}}
    assert not check_vad_update(old, copy.deepcopy(old))
    assert not check_vad_update(old, {"selected_module": {}})
    new = copy.deepcopy(old)
    new["VAD"]["first"]["max_audio_duration_ms"] = 30000
    assert check_vad_update(old, new)
    assert check_vad_update(old, {"selected_module": {"VAD": "second"}, "VAD": {"second": old["VAD"]["first"]}})


def test_silero_still_requires_its_file():
    with pytest.raises(ProviderProfileError, match="VAD.model_path"):
        validate_provider_config("VAD", {"type": "silero"}, require_ready=True)


def test_global_device_vad_startup_needs_no_silero_artifact(monkeypatch):
    from core.utils.modules_initialize import initialize_modules
    import config.provider_profile as profile
    monkeypatch.setattr(profile, "vad_model_path", Mock(side_effect=AssertionError("Silero artifact inspected")))
    config = {"read_config_from_api": True, "selected_module": {"VAD": "DeviceVAD"},
              "VAD": {"DeviceVAD": {"type": "device"}}}
    assert initialize_modules(Mock(), config, init_vad=True)["vad"].device_controlled is True


@pytest.mark.asyncio
async def test_abort_discards_device_turn_before_next_start():
    from core.handle.abortHandle import handleAbortMessage
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = Mock()
    conn.websocket = SimpleNamespace(send=AsyncMock())
    conn.session_id = "synthetic-session"
    conn.clear_queues = Mock()
    conn.clearSpeakStatus = Mock()
    handler = ListenTextMessageHandler()
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    conn.asr_audio.append(b"cancelled-question")
    await handleAbortMessage(conn)
    assert conn.asr_audio == []
    assert not conn.vad.is_listening(conn)
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    assert conn.vad.is_listening(conn)
    assert conn.asr_audio == []


@pytest.mark.asyncio
async def test_device_cannot_switch_to_automatic_mode_via_detect_message():
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = Mock()
    handler = ListenTextMessageHandler()
    await handler.handle(conn, {"state": "start", "mode": "manual"})
    await handler.handle(conn, {"state": "detect", "mode": "auto"})
    conn.close.assert_awaited_once()
    assert not conn.vad.is_listening(conn)


@pytest.mark.asyncio
async def test_in_flight_frame_from_aborted_turn_cannot_enter_next_question():
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = SimpleNamespace(receive_audio=AsyncMock(side_effect=lambda c, pcm, voice: c.asr_audio.append(pcm)))
    conn.client_listen_mode = "manual"
    conn.vad.start_listening(conn)
    old_frame = conn.vad.queue_audio(conn, b"old-question")
    conn.vad.stop_listening(conn)
    conn.reset_audio_states()
    conn.vad.start_listening(conn)
    await handleAudioMessage(conn, old_frame)
    conn.asr.receive_audio.assert_not_called()
    current = conn.vad.queue_audio(conn, b"current-question")
    await handleAudioMessage(conn, current)
    assert conn.asr_audio == [b"current-question"]


def test_receive_budget_limits_queue_even_when_worker_is_slow():
    from core.providers.vad.device import DeviceVadLimitError
    conn = connection(vad.create_instance("device", {"type": "device", "max_audio_duration_ms": 1000}))
    conn.client_listen_mode = "manual"
    conn.vad.start_listening(conn)
    conn.vad.queue_audio(conn, b"\0\0" * 16000)
    with pytest.raises(DeviceVadLimitError):
        conn.vad.queue_audio(conn, b"\0\0")
    assert not conn.vad.is_listening(conn)


@pytest.mark.parametrize("gateway", [False, True])
@pytest.mark.asyncio
async def test_both_audio_routes_use_turn_tagging_and_ignore_closed_turns(gateway):
    conn = connection(vad.create_instance("device", {"type": "device"}))
    conn.asr = Mock()
    conn.client_listen_mode = "manual"
    conn.bind_completed_event = asyncio.Event()
    conn.bind_completed_event.set()
    conn.need_bind = False
    conn.conn_from_mqtt_gateway = gateway
    conn._decode_opus_packet = Mock(return_value=b"\0\1" * 960)
    conn._queue_asr_audio = ConnectionHandler._queue_asr_audio.__get__(conn)
    conn._process_mqtt_audio_message = ConnectionHandler._process_mqtt_audio_message.__get__(conn)
    packet = bytes(16) + b"opus-fixture" if gateway else b"opus-fixture"
    await ConnectionHandler._route_message(conn, packet)
    conn._decode_opus_packet.assert_not_called()
    conn.vad.start_listening(conn)
    await ConnectionHandler._route_message(conn, packet)
    frame = conn.asr_audio_queue.get_nowait()
    assert frame.pcm == b"\0\1" * 960
    assert frame.turn_id == conn._device_vad_turn_id
    conn.vad.stop_listening(conn)
    await ConnectionHandler._route_message(conn, packet)
    assert conn.asr_audio_queue.empty()
