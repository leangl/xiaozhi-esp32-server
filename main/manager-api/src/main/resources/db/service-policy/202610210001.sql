-- Forward-only policy metadata. No assistant, history, voice or secret is deleted.
CREATE TABLE IF NOT EXISTS ai_service_remediation (
    model_id VARCHAR(32) NOT NULL PRIMARY KEY,
    reason_code VARCHAR(64) NOT NULL,
    first_detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Removed SMS transport cannot satisfy a legacy mandatory-SMS setting. Password
-- registration/CAPTCHA remain available; SMS-only recovery remains unavailable.
UPDATE sys_params SET param_value = 'false'
WHERE param_code = 'server.enable_mobile_register' AND param_value <> 'false';
