package xiaozhi.modules.security.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.mockito.MockedStatic;
import org.springframework.test.util.ReflectionTestUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.Sm2DecryptUtil;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.security.controller.LoginController;
import xiaozhi.modules.security.dto.LoginDTO;
import xiaozhi.modules.security.dto.SmsVerificationDTO;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.security.service.SysUserTokenService;
import xiaozhi.modules.security.password.PasswordUtils;
import xiaozhi.common.page.TokenDTO;
import xiaozhi.common.utils.Result;
import com.google.common.cache.Cache;
import xiaozhi.modules.sms.service.imp.UnavailableSmsService;
import xiaozhi.modules.sys.dto.RetrievePasswordDTO;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.dao.SysParamsDao;
import xiaozhi.modules.sys.redis.SysParamsRedis;
import xiaozhi.modules.sys.service.*;
import xiaozhi.modules.sys.service.impl.SysParamsServiceImpl;
import xiaozhi.modules.agent.service.AgentPluginMappingService;

class UnavailableSmsTest {
    private MockedStatic<MessageUtils> messages;

    @BeforeEach
    void messageLookupWithoutApplicationContext() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt())).thenReturn("Feature unavailable");
    }

    @AfterEach
    void closeMessageLookup() {
        messages.close();
    }
    @Test
    void unavailableTransportHasNoSuccessPath() {
        var service = new UnavailableSmsService();
        assertFalse(service.isAvailable());
        assertEquals(ErrorCode.MOBILE_REGISTER_DISABLED, assertThrows(RenException.class,
                () -> service.sendVerificationCodeSms("synthetic-phone", "000000")).getCode());
    }

    @Test
    void unavailableSendAndStaleCodeDoNotTouchRedisOrConfiguration() {
        var service = new CaptchaServiceImpl();
        var redis = mock(RedisUtils.class);
        var params = mock(SysParamsService.class);
        ReflectionTestUtils.setField(service, "redisUtils", redis);
        ReflectionTestUtils.setField(service, "sysParamsService", params);
        ReflectionTestUtils.setField(service, "smsService", new UnavailableSmsService());
        assertFalse(service.isSmsAvailable());
        assertEquals(ErrorCode.MOBILE_REGISTER_DISABLED, assertThrows(RenException.class,
                () -> service.sendSMSValidateCode("synthetic-phone")).getCode());
        assertFalse(service.validateSMSValidateCode("synthetic-phone", "000000", false));
        verifyNoInteractions(redis, params);
    }

    @Test
    void smsEndpointsRejectBeforeCaptchaAndRecoveryAccountLookup() {
        var users = mock(SysUserService.class);
        var captcha = mock(CaptchaService.class);
        var params = mock(SysParamsService.class);
        var controller = new LoginController(users, mock(SysUserTokenService.class),
                captcha, params, mock(SysDictDataService.class));
        assertEquals(ErrorCode.MOBILE_REGISTER_DISABLED, assertThrows(RenException.class,
                () -> controller.smsVerification(new SmsVerificationDTO())).getCode());
        assertEquals(ErrorCode.RETRIEVE_PASSWORD_DISABLED, assertThrows(RenException.class,
                () -> controller.retrievePassword(new RetrievePasswordDTO())).getCode());
        verifyNoInteractions(users, params);
        verify(captcha, times(2)).isSmsAvailable();
        verifyNoMoreInteractions(captcha);
    }

    @Test
    void staleMobileFlagDoesNotSilentlyWeakenRegistration() {
        var users = mock(SysUserService.class);
        when(users.getAllowUserRegister()).thenReturn(true);
        var captcha = mock(CaptchaService.class);
        var params = mock(SysParamsService.class);
        when(params.getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class))
                .thenReturn(true);
        var controller = new LoginController(users, mock(SysUserTokenService.class),
                captcha, params, mock(SysDictDataService.class));
        assertEquals(ErrorCode.MOBILE_REGISTER_DISABLED, assertThrows(RenException.class,
                () -> controller.register(new LoginDTO())).getCode());
        verify(users, never()).save(any());
        verify(captcha, never()).validateSMSValidateCode(any(), any(), anyBoolean());
    }

    @Test
    void passwordRegistrationStillUsesTheExistingDecryptionAndCaptchaBoundary() {
        var users = mock(SysUserService.class);
        when(users.getAllowUserRegister()).thenReturn(true);
        var captcha = mock(CaptchaService.class);
        var params = mock(SysParamsService.class);
        when(params.getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class))
                .thenReturn(false);
        var controller = new LoginController(users, mock(SysUserTokenService.class),
                captcha, params, mock(SysDictDataService.class));
        var request = new LoginDTO();
        request.setUsername("synthetic-user");
        request.setPassword("encrypted-fixture");
        request.setCaptchaId("synthetic-captcha");
        try (var decrypt = mockStatic(Sm2DecryptUtil.class)) {
            decrypt.when(() -> Sm2DecryptUtil.decryptAndValidateCaptcha("encrypted-fixture",
                    "synthetic-captcha", captcha, params)).thenReturn("Synthetic-Password!42");
            controller.register(request);
            decrypt.verify(() -> Sm2DecryptUtil.decryptAndValidateCaptcha("encrypted-fixture",
                    "synthetic-captcha", captcha, params));
        }
        verify(users).save(argThat((SysUserDTO dto) -> dto.getUsername().equals("synthetic-user")
                && dto.getPassword().equals("Synthetic-Password!42")));
        verifyNoInteractions(captcha);
    }

    @Test
    void passwordLoginStillChecksTheHashAndCreatesAnAccountToken() {
        var users = mock(SysUserService.class);
        var tokens = mock(SysUserTokenService.class);
        var captcha = mock(CaptchaService.class);
        var params = mock(SysParamsService.class);
        var user = new SysUserDTO();
        user.setId(42L);
        user.setPassword(PasswordUtils.encode("Synthetic-Password!42"));
        when(users.getByUsername("synthetic-user")).thenReturn(user);
        var token = new Result<TokenDTO>().ok(new TokenDTO());
        when(tokens.createToken(42L)).thenReturn(token);
        var controller = new LoginController(users, tokens, captcha, params, mock(SysDictDataService.class));
        var request = new LoginDTO();
        request.setUsername("synthetic-user");
        request.setPassword("encrypted-fixture");
        request.setCaptchaId("synthetic-captcha");
        try (var decrypt = mockStatic(Sm2DecryptUtil.class)) {
            decrypt.when(() -> Sm2DecryptUtil.decryptAndValidateCaptcha("encrypted-fixture",
                    "synthetic-captcha", captcha, params)).thenReturn("Synthetic-Password!42");
            assertSame(token, controller.login(request));
        }
        verify(tokens).createToken(42L);
        verifyNoInteractions(captcha);
    }

    @Test
    @SuppressWarnings("unchecked")
    void localCaptchaValidationDoesNotRequireSms() {
        var service = new CaptchaServiceImpl();
        ReflectionTestUtils.setField(service, "smsService", new UnavailableSmsService());
        var cache = (Cache<String, String>) ReflectionTestUtils.getField(service, "localCache");
        cache.put("fixture-captcha", "Ab123");
        assertTrue(service.validate("fixture-captcha", "ab123", true));
        assertFalse(service.validate("fixture-captcha", "ab123", true));
        assertFalse(service.isSmsAvailable());
    }

    @Test
    void retiredSettingsAndActivationAreRejectedBeforeDatabaseOrCacheWrites() {
        var cache = mock(SysParamsRedis.class);
        var dao = mock(SysParamsDao.class);
        var service = new SysParamsServiceImpl(cache, mock(AgentPluginMappingService.class));
        ReflectionTestUtils.setField(service, "baseDao", dao);
        for (String code : new String[] {"aliyun.sms.access_key_id", "ALIYUN.SMS.access_key_secret",
                Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue()}) {
            assertEquals(ErrorCode.MOBILE_REGISTER_DISABLED, assertThrows(RenException.class,
                    () -> service.updateValueByCode(code, "true")).getCode());
            var dto = new SysParamsDTO();
            dto.setParamCode(code);
            dto.setParamValue("true");
            assertThrows(RenException.class, () -> service.save(dto));
            assertThrows(RenException.class, () -> service.update(dto));
        }
        verifyNoInteractions(dao, cache);
    }
}
