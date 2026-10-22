package xiaozhi.modules.sms.service.imp;

import org.springframework.stereotype.Service;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.sms.service.SmsService;

/** No remote SMS operator is configured; never pretend a message was sent. */
@Service
public class UnavailableSmsService implements SmsService {
    @Override
    public void sendVerificationCodeSms(String phone, String verificationCode) {
        throw new RenException(ErrorCode.MOBILE_REGISTER_DISABLED);
    }
}
