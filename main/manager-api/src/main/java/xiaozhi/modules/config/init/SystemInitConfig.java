package xiaozhi.modules.config.init;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.RenException;

import jakarta.annotation.PostConstruct;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.device.service.DeviceAddressBookService;
import xiaozhi.modules.sys.service.SysParamsService;

@Configuration
@DependsOn("liquibase")
@Slf4j
public class SystemInitConfig {

    @Autowired
    private ServicePolicyUpgrade servicePolicyUpgrade;

    @Autowired
    private SysParamsService sysParamsService;

    @Autowired
    private ConfigService configService;

    @Autowired
    private RedisUtils redisUtils;

    @Autowired
    private DeviceAddressBookService deviceAddressBookService;

    @PostConstruct
    public void init() {
        // Check the version
        String redisVersion = (String) redisUtils.get(RedisKeys.getVersionKey());
        if (!Constant.VERSION.equals(redisVersion)) {
            // Clear Redis if the version differs
            redisUtils.emptyAll();
            // Store the new version
            redisUtils.set(RedisKeys.getVersionKey(), Constant.VERSION);
        }

        sysParamsService.initServerSecret();
        servicePolicyUpgrade.apply();
        try {
            configService.getConfig(false);
        } catch (RenException unavailable) {
            // Administration must remain reachable to configure explicit approved
            // replacements. Voice activation still enforces the runtime policy.
            log.warn("Voice configuration is not ready; select approved ASR/LLM/TTS settings in management.");
        }

        // Initialize the device address book cache
        deviceAddressBookService.refreshCache();
    }
}
