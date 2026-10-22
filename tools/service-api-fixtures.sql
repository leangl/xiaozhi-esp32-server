-- Synthetic, disposable candidate ONLY. Apply through service-api-smoke.mjs
-- --seed-fixtures after schema/forward-policy migration, never with raw mysql.
-- The client checks exact Docker project/fixture labels and an empty user,
-- assistant, device, history, audio and snapshot database before executing this.
-- No user/model assignments are copied from another database.
START TRANSACTION;

INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark)
VALUES (900000000000000101, 'validation.api_smoke_fixture',
        'service-policy-rehearsal-20261021-v1', 'string', 1, 'Synthetic smoke fixture marker');
UPDATE sys_params SET param_value = 'true' WHERE param_code = 'server.allow_user_register';
UPDATE sys_params SET param_value = 'false' WHERE param_code = 'server.enable_mobile_register';
UPDATE sys_params SET param_value = REPEAT('a', 64) WHERE param_code = 'server.secret';
-- The synthetic voice clients use the optional JSON ping as an audio queue
-- ordering barrier. Enable that existing feature only in this fresh fixture.
UPDATE sys_params SET param_value = 'true' WHERE param_code = 'enable_websocket_ping';

-- This exact on-image path is explicitly approved for the isolated voice image.
UPDATE ai_model_config
SET config_json = JSON_SET(config_json, '$.model_path',
    'models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx')
WHERE id = 'VAD_SileroVAD';

-- Only baseline default flags change; no user choices exist at this point.
-- SLM's create path chooses the enabled default LLM, independently of template.
UPDATE ai_model_config SET is_default = 0 WHERE UPPER(model_type) = 'LLM';
INSERT INTO ai_model_config
    (id, model_type, model_code, model_name, is_default, is_enabled, config_json, sort, remark)
VALUES
('SMOKE_ASR_OPENAI', 'ASR', 'OpenAIASR', 'Synthetic ASR', 1, 1,
 JSON_OBJECT('type', 'openai', 'base_url', 'http://127.0.0.1:19200/v1/audio/transcriptions',
             'model_name', 'smoke-asr', 'api_key', 'local-only', 'output_dir', 'tmp/asr'), 0, 'Synthetic only'),
('SMOKE_LLM_OPENAI', 'LLM', 'OpenAILLM', 'Synthetic LLM', 1, 1,
 JSON_OBJECT('type', 'openai', 'base_url', 'http://127.0.0.1:19200/v1',
             'model_name', 'smoke-llm', 'api_key', 'local-only', 'timeout', 4), 0, 'Synthetic only'),
('SMOKE_VLLM_OPENAI', 'VLLM', 'OpenAIVLLM', 'Synthetic vision', 1, 1,
 JSON_OBJECT('type', 'openai', 'base_url', 'http://127.0.0.1:19200/v1',
             'model_name', 'smoke-llm', 'api_key', 'local-only'), 0, 'Synthetic only'),
('SMOKE_TTS_OPENAI', 'TTS', 'OpenAITTS', 'Synthetic TTS', 1, 1,
 JSON_OBJECT('type', 'openai', 'api_url', 'http://127.0.0.1:19200/v1/audio/speech',
             'model', 'smoke-tts', 'voice', 'alloy', 'format', 'wav',
             'api_key', 'local-only', 'output_dir', 'tmp/tts'), 0, 'Synthetic only'),
('SMOKE_MEMORY_NONE', 'Memory', 'nomem', 'Synthetic no memory', 1, 1,
 JSON_OBJECT('type', 'nomem'), 0, 'Synthetic only'),
('SMOKE_INTENT_NONE', 'Intent', 'nointent', 'Synthetic no intent', 1, 1,
 JSON_OBJECT('type', 'nointent'), 0, 'Synthetic only'),
-- Deliberately unavailable historical selection, never used by a runtime.
('SMOKE_REMOVED_ASR', 'ASR', 'FunASR', 'Synthetic removed ASR', 0, 0,
 JSON_OBJECT('type', 'funasr', 'base_url', 'http://127.0.0.1:19200'), 0, 'Rejection fixture only');

INSERT INTO ai_tts_voice
    (id, tts_model_id, name, tts_voice, languages, voice_demo, sort, remark)
VALUES ('SMOKE_VOICE_ALLOY', 'SMOKE_TTS_OPENAI', 'Synthetic alloy', 'alloy', 'English', NULL, 0, 'Synthetic only');

-- Keep legacy template selections intact. Move baseline display order only so
-- the newly inserted template is unambiguously first (sort is unsigned).
UPDATE ai_agent_template SET sort = COALESCE(sort, 0) + 1;
INSERT INTO ai_agent_template
    (id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id,
     vllm_model_id, tts_model_id, tts_voice_id, tts_language, mem_model_id,
     intent_model_id, system_prompt, chat_history_conf, lang_code, language, sort)
VALUES ('SMOKE_APPROVED_TEMPLATE', 'synthetic-smoke', 'Synthetic smoke assistant',
        'SMOKE_ASR_OPENAI', 'VAD_SileroVAD', 'SMOKE_LLM_OPENAI', 'SMOKE_VLLM_OPENAI',
        'SMOKE_TTS_OPENAI', 'SMOKE_VOICE_ALLOY', 'English', 'SMOKE_MEMORY_NONE',
        'SMOKE_INTENT_NONE', 'Reply with one short synthetic sentence.', 2, 'en_US', 'English', 0);
COMMIT;
