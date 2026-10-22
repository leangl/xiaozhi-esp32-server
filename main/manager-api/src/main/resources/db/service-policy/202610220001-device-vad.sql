-- Add an opt-in choice only. Never change defaults, assistants, or existing rows.
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
SELECT 'SYSTEM_VAD_DeviceVAD', 'VAD', 'device', 'Device VAD (no server inference)',
       '[{"key":"max_audio_duration_ms","label":"Maximum question duration (ms, 1000-300000)","type":"number"}]',
       2, 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_provider WHERE id = 'SYSTEM_VAD_DeviceVAD');

INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, remark, sort, creator, create_date, updater, update_date)
SELECT 'VAD_DeviceVAD', 'VAD', 'DeviceVAD', 'Device VAD (no server inference)', 0, 1,
       '{"type":"device","max_audio_duration_ms":60000}',
       'The device must send manual listen/start and listen/stop. No Silero model is loaded. Overlong turns are discarded.',
       2, 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'VAD_DeviceVAD');
