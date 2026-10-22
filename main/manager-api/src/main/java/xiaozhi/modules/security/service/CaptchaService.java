package xiaozhi.modules.security.service;

import java.io.IOException;

import jakarta.servlet.http.HttpServletResponse;

/**
 * Verification code
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public interface CaptchaService {

    /** Availability is independent of stale database flags or SMS codes. */
    default boolean isSmsAvailable() {
        return false;
    }

    /**
     * Image verification code
     */
    void create(HttpServletResponse response, String uuid) throws IOException;

    /**
     * Verification code validation
     * 
     * @param uuid   uuid
     * @param code verification code
     * @param delete whether to delete the verification code
     * @return true on success, false on failure
     */
    boolean validate(String uuid, String code, Boolean delete);

    /**
     * Send an SMS verification code
     * 
     * @param phone phone number
     */
    void sendSMSValidateCode(String phone);

    /**
     * Validate the SMS verification code
     * 
     * @param phone phone number
     * @param code verification code
     * @param delete whether to delete the verification code
     * @return true on success, false on failure
     */
    boolean validateSMSValidateCode(String phone, String code, Boolean delete);
}
