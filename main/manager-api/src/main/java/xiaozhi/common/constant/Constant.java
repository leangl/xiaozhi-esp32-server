package xiaozhi.common.constant;

import lombok.Getter;

/**
 * Constants
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public interface Constant {
    /**
     * Success
     */
    int SUCCESS = 1;
    /**
     * Failure
     */
    int FAIL = 0;
    /**
     * OK
     */
    String OK = "OK";
    /**
     * User identifier
     */
    String USER_KEY = "userId";
    /**
     * Menu root node identifier
     */
    Long MENU_ROOT = 0L;
    /**
     * Department root node identifier
     */
    Long DEPT_ROOT = 0L;
    /**
     * Data dictionary root node identifier
     */
    Long DICT_ROOT = 0L;
    /**
     * Ascending
     */
    String ASC = "asc";
    /**
     * Descending
     */
    String DESC = "desc";
    /**
     * Creation timestamp field name
     */
    String CREATE_DATE = "create_date";

    /**
     * Creation timestamp field name
     */
    String ID = "id";

    /**
     * Data access filtering
     */
    String SQL_FILTER = "sqlFilter";

    /**
     * Current page number
     */
    String PAGE = "page";
    /**
     * Records per page
     */
    String LIMIT = "limit";
    /**
     * Sort field
     */
    String ORDER_FIELD = "orderField";
    /**
     * Sort direction
     */
    String ORDER = "order";

    /**
     * Authorization header identifier
     */
    String AUTHORIZATION = "Authorization";

    /**
     * Server secret
     */
    String SERVER_SECRET = "server.secret";

    /**
     * SM2 public key
     */
    String SM2_PUBLIC_KEY = "server.public_key";

    /**
     * SM2 private key
     */
    String SM2_PRIVATE_KEY = "server.private_key";

    /**
     * WebSocket URL
     */
    String SERVER_WEBSOCKET = "server.websocket";

    /**
     * MQTT gateway configuration
     */
    String SERVER_MQTT_GATEWAY = "server.mqtt_gateway";

    /**
     * OTA URL
     */
    String SERVER_OTA = "server.ota";

    /**
     * Whether user registration is allowed
     */
    String SERVER_ALLOW_USER_REGISTER = "server.allow_user_register";

    /**
     * Console URL displayed with the six-digit verification code
     */
    String SERVER_FRONTED_URL = "server.fronted_url";

    /**
     * Path separator
     */
    String FILE_EXTENSION_SEG = ".";

    /**
     * MCP access point path
     */
    String SERVER_MCP_ENDPOINT = "server.mcp_endpoint";

    /**
     * MCP access point path
     */
    String SERVER_VOICE_PRINT = "server.voice_print";

    /**
     * MQTT secret
     */
    String SERVER_MQTT_SECRET = "server.mqtt_signature_key";

    /**
     * WebSocket authentication toggle
     */
    String SERVER_AUTH_ENABLED = "server.auth.enabled";

    /**
     * System feature menu configuration
     */
    String SYSTEM_WEB_MENU = "system-web.menu";

    /**
     * No memory
     */
    String MEMORY_NO_MEM = "Memory_nomem";

    /**
     * Report chat history only (without memory summarization)
     */
    String MEMORY_MEM_REPORT_ONLY = "Memory_mem_report_only";

    /**
     * Mem0AI memory
     */
    String MEMORY_MEM0AI = "Memory_mem0ai";

    /**
     * PowerMem memory
     */
    String MEMORY_POWERMEM = "Memory_powermem";

    /**
     * Volcengine dual-channel voice cloning
     */
    String VOICE_CLONE_HUOSHAN_DOUBLE_STREAM = "huoshan_double_stream";

    /**
     * RAG configuration type
     */
    String RAG_CONFIG_TYPE = "RAG";

    enum SysBaseParam {
        /**
         * ICP registration number
         */
        BEIAN_ICP_NUM("server.beian_icp_num"),
        /**
         * Public security registration number
         */
        BEIAN_GA_NUM("server.beian_ga_num"),
        /**
         * System name
         */
        SERVER_NAME("server.name");

        private String value;

        SysBaseParam(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    /**
     * Training status
     */
    enum TrainStatus {
        /**
         * Not trained
         */
        NOT_TRAINED(0),
        /**
         * Training in progress
         */
        TRAINING(1),
        /**
         * Trained
         */
        TRAINED(2),
        /**
         * Training failed
         */
        TRAIN_FAILED(3);

        private final int code;

        TrainStatus(int code) {
            this.code = code;
        }

        public int getCode() {
            return code;
        }
    }

    /**
     * System SMS
     */
    enum SysMSMParam {
        /**
         * Maximum SMS messages per phone number
         */
        SERVER_SMS_MAX_SEND_COUNT("server.sms_max_send_count"),
        /**
         * Whether phone registration is enabled
         */
        SERVER_ENABLE_MOBILE_REGISTER("server.enable_mobile_register");

        private String value;

        SysMSMParam(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    /**
     * Data status
     */
    enum DataOperation {
        /**
         * Inserted
         */
        INSERT("I"),
        /**
         * Modified
         */
        UPDATE("U"),
        /**
         * Deleted
         */
        DELETE("D");

        private String value;

        DataOperation(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    // Localized labels: no recording, text only, and text plus audio. Keep these Chinese UI values and numeric codes.
    @Getter
    enum ChatHistoryConfEnum {
        IGNORE(0, "不记录"),
        RECORD_TEXT(1, "记录文本"),
        RECORD_TEXT_AUDIO(2, "文本音频都记录");

        private final int code;
        private final String name;

        ChatHistoryConfEnum(int code, String name) {
            this.code = code;
            this.name = name;
        }
    }

    /**
     * Version number
     */
    public static final String VERSION = "0.9.7";

    /**
     * Invalid firmware URL
     */
    String INVALID_FIRMWARE_URL = "http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL";

    /**
     * Dictionary type
     */
    enum DictType {
        /**
         * Phone country code
         */
        MOBILE_AREA("MOBILE_AREA");

        private String value;

        DictType(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }
}
