"""Opt-in catalog expansion is retry-safe and preserves existing selections."""
import json
from pathlib import Path
import sqlite3

import yaml


RESOURCES = Path(__file__).resolve().parents[3] / "manager-api/src/main/resources/db"


def test_device_catalog_is_additive_idempotent_and_wired_after_existing_changes():
    path = RESOURCES / "service-policy/202610220001-device-vad.sql"
    sql = path.read_text()
    changelog = yaml.safe_load((RESOURCES / "service-policy.changelog.yaml").read_text())["databaseChangeLog"]
    assert changelog[-1]["changeSet"]["id"] == 202610220001
    assert changelog[-1]["changeSet"]["changes"][0]["sqlFile"]["path"].endswith(path.name)
    # SQLite exercises additive/retry semantics; the statements use portable
    # INSERT/SELECT/NOT EXISTS. MySQL/Liquibase execution is a separate gate.
    db = sqlite3.connect(":memory:")
    db.create_function("NOW", 0, lambda: "fixture-date")
    db.executescript("""
        CREATE TABLE ai_model_provider (id TEXT PRIMARY KEY, model_type TEXT, provider_code TEXT,
          name TEXT, fields TEXT, sort INTEGER, creator INTEGER, create_date TEXT, updater INTEGER, update_date TEXT);
        CREATE TABLE ai_model_config (id TEXT PRIMARY KEY, model_type TEXT, model_code TEXT,
          model_name TEXT, is_default INTEGER, is_enabled INTEGER, config_json TEXT, remark TEXT,
          sort INTEGER, creator INTEGER, create_date TEXT, updater INTEGER, update_date TEXT);
        CREATE TABLE ai_agent (id TEXT PRIMARY KEY, vad_model_id TEXT);
        INSERT INTO ai_model_config (id, model_type, is_default, config_json)
          VALUES ('VAD_SileroVAD', 'VAD', 1, '{"type":"silero","threshold":0.7}');
        INSERT INTO ai_agent VALUES ('existing-assistant', 'VAD_SileroVAD');
    """)
    before = db.execute("SELECT * FROM ai_model_config").fetchall()
    db.executescript(sql)
    first = db.execute("SELECT * FROM ai_model_config ORDER BY id").fetchall()
    db.executescript(sql)
    assert db.execute("SELECT * FROM ai_model_config ORDER BY id").fetchall() == first
    assert db.execute("SELECT * FROM ai_model_config WHERE id='VAD_SileroVAD'").fetchall() == before
    assert db.execute("SELECT vad_model_id FROM ai_agent").fetchone() == ("VAD_SileroVAD",)
    row = db.execute("SELECT is_default,is_enabled,config_json FROM ai_model_config WHERE id='VAD_DeviceVAD'").fetchone()
    assert row[:2] == (0, 1)
    assert json.loads(row[2]) == {"type": "device", "max_audio_duration_ms": 60000}
    fields = json.loads(db.execute("SELECT fields FROM ai_model_provider WHERE provider_code='device'").fetchone()[0])
    assert fields[0]["key"] == "max_audio_duration_ms"
    # A later operator edit is preserved on SQL retry too.
    db.execute("UPDATE ai_model_config SET config_json='{}' WHERE id='VAD_DeviceVAD'")
    db.executescript(sql)
    assert db.execute("SELECT config_json FROM ai_model_config WHERE id='VAD_DeviceVAD'").fetchone() == ("{}",)
