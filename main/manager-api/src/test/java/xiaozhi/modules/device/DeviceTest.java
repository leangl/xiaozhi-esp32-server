package xiaozhi.modules.device;

import java.util.HashMap;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.service.SysUserService;

@Slf4j
@SpringBootTest
@ActiveProfiles("dev")
@DisplayName("Device tests")
// The Chinese hardware-model string is device-data fixture content, not a test description.
public class DeviceTest {

    @Autowired
    private RedisUtils redisUtils;
    @Autowired
    private SysUserService sysUserService;

    @Test
    public void testRejectWeakPassword() {
        SysUserDTO userDTO = new SysUserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("weak-password-123");

        RenException exception = Assertions.assertThrows(RenException.class, () -> sysUserService.save(userDTO));
        Assertions.assertEquals(ErrorCode.PASSWORD_WEAK_ERROR, exception.getCode());
    }

    @Test
    @DisplayName("Test writing device information")
    public void testWriteDeviceInfo() {
        log.info("Starting device information write test...");
        // Mock device MAC address
        String macAddress = "00:11:22:33:44:66";
        // Mock device verification code
        String deviceCode = "123456";

        HashMap<String, Object> map = new HashMap<>();
        map.put("mac_address", macAddress);
        map.put("activation_code", deviceCode);
        map.put("board", "硬件型号");
        map.put("app_version", "0.3.13");

        String safeDeviceId = macAddress.replace(":", "_").toLowerCase();
        String cacheDeviceKey = String.format("ota:activation:data:%s", safeDeviceId);
        redisUtils.set(cacheDeviceKey, map, 300);

        String redisKey = "ota:activation:code:" + deviceCode;
        log.info("Redis Key: {}", redisKey);

        // Write device information to Redis
        redisUtils.set(redisKey, macAddress, 300);
        log.info("Device information written to Redis");

        // Verify the write succeeded
        String savedMacAddress = (String) redisUtils.get(redisKey);
        log.info("MAC address read from Redis: {}", savedMacAddress);

        // Verify with assertions
        Assertions.assertNotNull(savedMacAddress, "MAC address read from Redis must not be null");
        Assertions.assertEquals(macAddress, savedMacAddress, "Saved MAC address differs from the original");

        log.info("Test completed");
    }
}
