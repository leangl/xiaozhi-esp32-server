package xiaozhi.modules.sms.service;

/**
 * SMS service interface
 *
 * @author zjy
 * @since 2025-05-12
 */
public interface SmsService {

    /** A replacement must explicitly opt in only after it is configured. */
    default boolean isAvailable() {
        return false;
    }

    /**
     * Send the verification SMS
     * @param phone phone number
     * @param VerificationCode verification code
     */
    void sendVerificationCodeSms(String phone, String VerificationCode) ;
}
