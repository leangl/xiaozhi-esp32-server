package xiaozhi.common.redis;

/**
 * Redis key constants
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public class RedisKeys {
    /**
     * System parameter key
     */
    public static String getSysParamsKey() {
        return "sys:params";
    }

    /**
     * Verification code key
     */
    public static String getCaptchaKey(String uuid) {
        return "sys:captcha:" + uuid;
    }

    /**
     * Unregistered device verification code key
     */
    public static String getDeviceCaptchaKey(String captcha) {
        return "sys:device:captcha:" + captcha;
    }

    /**
     * User ID key
     */
    public static String getUserIdKey(Long userid) {
        return "sys:username:id:" + userid;
    }

    /**
     * Model name key
     */
    public static String getModelNameById(String id) {
        return "model:name:" + id;
    }

    /**
     * Model configuration key
     */
    public static String getModelConfigById(String id) {
        return "model:data:" + id;
    }

    /**
     * Get the voice name cache key
     */
    public static String getTimbreNameById(String id) {
        return "timbre:name:" + id;
    }

    /**
     * Get the device count cache key
     */
    public static String getAgentDeviceCountById(String id) {
        return "agent:device:count:" + id;
    }

    /**
     * Get the agent last connection time cache key
     */
    public static String getAgentDeviceLastConnectedAtById(String id) {
        return "agent:device:lastConnected:" + id;
    }

    /**
     * Get the system configuration cache key
     */
    public static String getServerConfigKey() {
        return "server:config";
    }

    /**
     * Get the voice details cache key
     */
    public static String getTimbreDetailsKey(String id) {
        return "timbre:details:" + id;
    }

    /**
     * Get the version key
     */
    public static String getVersionKey() {
        return "sys:version";
    }

    /**
     * OTA firmware ID key
     */
    public static String getOtaIdKey(String uuid) {
        return "ota:id:" + uuid;
    }

    /**
     * OTA firmware download count key
     */
    public static String getOtaDownloadCountKey(String uuid) {
        return "ota:download:count:" + uuid;
    }

    /**
     * Get the dictionary data cache key
     */
    public static String getDictDataByTypeKey(String dictType) {
        return "sys:dict:data:" + dictType;
    }

    /**
     * Get the agent audio ID cache key
     */
    public static String getAgentAudioIdKey(String uuid) {
        return "agent:audio:id:" + uuid;
    }

    /**
     * Get the SMS verification code cache key
     */
    public static String getSMSValidateCodeKey(String phone) {
        return "sms:Validate:Code:" + phone;
    }

    /**
     * Get the last SMS verification code send time cache key
     */
    public static String getSMSLastSendTimeKey(String phone) {
        return "sms:Validate:Code:" + phone + ":last_send_time";
    }

    /**
     * Get today's SMS verification code send count cache key
     */
    public static String getSMSTodayCountKey(String phone) {
        return "sms:Validate:Code:" + phone + ":today_count";
    }

    /**
     * Chat history UUID mapping key
     */
    public static String getChatHistoryKey(String uuid) {
        return "agent:chat:history:" + uuid;
    }

    /**
     * Get the voice cloning audio ID cache key
     */
    public static String getVoiceCloneAudioIdKey(String uuid) {
        return "voiceClone:audio:id:" + uuid;
    }

    /**
     * Get the knowledge base cache key
     */
    public static String getKnowledgeBaseCacheKey(String datasetId) {
        return "knowledge:base:" + datasetId;
    }

    /**
     * Get the temporary device registration marker key
     */
    public static String getTmpRegisterMacKey(String deviceId) {
        return "tmp_register_mac:" + deviceId;
    }

    /**
     * OTA device binding
     */
    public static String getOtaActivationCode(String activationCode) {
        return "ota:activation:code:" + activationCode;
    }

    /**
     * OTA device MAC information lookup
     */
    public static String getOtaDeviceActivationInfo(String deviceId) {
        return "ota:activation:data:" + deviceId;
    }

    /**
     * OTA upload count
     */
    public static String getOtaUploadCountKey(Long username) {
        return "ota:upload:count:" + username;
    }

    /**
     * Device address book cache key
     */
    public static String getAddressBookKey() {
        return "device:address_book:all";
    }

}
