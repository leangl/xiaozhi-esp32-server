package xiaozhi.modules.config.service.impl;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.service.AgentContextProviderService;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.correctword.service.CorrectWordFileService;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.timbre.service.TimbreService;
import xiaozhi.modules.voiceclone.service.VoiceCloneService;

class ConfigServiceImplTest {

    @Test
    void cachedProviderConfigurationIsRejectedBeforeReturningSecretsToRuntime() {
        RedisUtils redisUtils = mock(RedisUtils.class);
        when(redisUtils.get(RedisKeys.getServerConfigKey())).thenReturn(Map.of("ASR", Map.of("alias",
                Map.of("type", "openai", "base_url", "https://unknown.example/secret", "api_key", "synthetic-secret"))));
        ConfigServiceImpl service = newService(mock(SysParamsService.class), redisUtils);
        var error = assertThrows(xiaozhi.common.exception.RenException.class, () -> service.getConfig(true));
        org.junit.jupiter.api.Assertions.assertFalse(error.getMessage().contains("secret"));
        org.junit.jupiter.api.Assertions.assertTrue(error.getMessage().startsWith("ASR configuration is unavailable"));
    }

    @Test
    void removedPluginSystemParametersAreNotAdvertisedAsRuntimeTools() {
        SysParamsService params = mock(SysParamsService.class);
        when(params.list(anyMap())).thenReturn(List.of(parameter("plugins.get_weather.api_key", "secret", "string"),
                parameter("plugins.play_music.music_dir", "./music", "string")));
        ConfigServiceImpl service = newService(params, mock(RedisUtils.class));
        Map<String, Object> config = new HashMap<>();
        ReflectionTestUtils.invokeMethod(service, "buildConfig", config);
        assertEquals(Map.of("play_music", Map.of("music_dir", "./music")), config.get("plugins"));
    }

    @Test
    void staleOptionalToolsAndContextBecomeInertWithoutBlockingUnrelatedCachedConfiguration() {
        RedisUtils redis = mock(RedisUtils.class);
        Map<String, Object> cached = new HashMap<>();
        cached.put("features", Map.of("enabled", true));
        cached.put("plugins", Map.of("hass_state", Map.of("base_url", "https://unknown.example", "api_key", "synthetic-secret"),
                "play_music", Map.of("music_dir", "./music")));
        cached.put("context_providers", List.of(Map.of("url", "https://unknown.example", "headers", Map.of("Authorization", "secret"))));
        when(redis.get(RedisKeys.getServerConfigKey())).thenReturn(cached);
        var result = newService(mock(SysParamsService.class), redis).getConfig(true);
        assertEquals(Map.of("play_music", Map.of("music_dir", "./music")), result.get("plugins"));
        assertEquals(List.of(), result.get("context_providers"));
        assertEquals(Map.of("enabled", true), result.get("features"));
        org.junit.jupiter.api.Assertions.assertFalse(result.toString().contains("secret"));
        assertEquals(2, ((Map<?, ?>) cached.get("plugins")).size());
    }

    @Test
    void cachedPolicyValidModelStillRequiresEnabledCurrentCatalogRow() {
        RedisUtils redis = mock(RedisUtils.class);
        when(redis.get(RedisKeys.getServerConfigKey())).thenReturn(Map.of("ASR", Map.of("disabled",
                Map.of("type", "openai", "base_url", "http://localhost:9999/v1"))));
        ConfigServiceImpl service = newService(mock(SysParamsService.class), redis);
        var models = (ModelConfigService) ReflectionTestUtils.getField(service, "modelConfigService");
        var disabled = new xiaozhi.modules.model.entity.ModelConfigEntity();
        disabled.setModelType("ASR");
        disabled.setIsEnabled(0);
        disabled.setConfigJson(new cn.hutool.json.JSONObject().set("type", "openai").set("base_url", "http://localhost:9999/v1"));
        when(models.getModelByIdFromCache("disabled")).thenReturn(disabled);
        assertThrows(xiaozhi.common.exception.RenException.class, () -> service.getConfig(true));
    }

    @Test
    void alreadyInstantiatedAsrHintCannotBypassUnavailableAssistantSelection() {
        ConfigServiceImpl service = newService(mock(SysParamsService.class), mock(RedisUtils.class));
        var devices = (DeviceService) ReflectionTestUtils.getField(service, "deviceService");
        var agents = (AgentService) ReflectionTestUtils.getField(service, "agentService");
        var models = (ModelConfigService) ReflectionTestUtils.getField(service, "modelConfigService");
        var device = new xiaozhi.modules.device.entity.DeviceEntity();
        device.setAgentId("agent");
        when(devices.getDeviceByMacAddress("synthetic-mac")).thenReturn(device);
        var agent = new xiaozhi.modules.agent.vo.AgentInfoVO();
        agent.setAsrModelId("legacy-asr");
        when(agents.getAgentById("agent")).thenReturn(agent);
        var legacy = new xiaozhi.modules.model.entity.ModelConfigEntity();
        legacy.setModelType("ASR");
        legacy.setIsEnabled(1);
        legacy.setConfigJson(new cn.hutool.json.JSONObject().set("type", "fun_local"));
        when(models.getModelByIdFromCache("legacy-asr")).thenReturn(legacy);
        assertThrows(xiaozhi.common.exception.RenException.class,
                () -> service.getAgentModels("synthetic-mac", Map.of("ASR", "legacy-asr")));
        org.mockito.Mockito.verifyNoInteractions(ReflectionTestUtils.getField(service, "timbreService"));
    }

    @Test
    void cachedServerConfigIsCheckedAsAStringKeyedMapWithoutChangingNestedValues() {
        RedisUtils redisUtils = mock(RedisUtils.class);
        Map<String, Object> nested = new HashMap<>();
        nested.put("enabled", true);
        Map<String, Object> cached = new HashMap<>();
        cached.put("features", nested);
        when(redisUtils.get(RedisKeys.getServerConfigKey())).thenReturn(cached);

        ConfigServiceImpl service = newService(mock(SysParamsService.class), redisUtils);

        Map<String, Object> result = service.getConfig(true);

        assertNotSame(cached, result);
        assertSame(nested, result.get("features"));
        assertEquals(true, ((Map<?, ?>) result.get("features")).get("enabled"));
    }

    @Test
    void nestedSystemParametersStillShareAndPopulateTheSameConfigBranch() {
        SysParamsService sysParamsService = mock(SysParamsService.class);
        SysParamsDTO enabled = parameter("server.features.enabled", "true", "boolean");
        SysParamsDTO labels = parameter("server.features.labels", "first;second", "array");
        when(sysParamsService.list(anyMap())).thenReturn(List.of(enabled, labels));
        ConfigServiceImpl service = newService(sysParamsService, mock(RedisUtils.class));
        Map<String, Object> config = new HashMap<>();

        Object returned = ReflectionTestUtils.invokeMethod(service, "buildConfig", config);

        assertSame(config, returned);
        Map<?, ?> server = assertInstanceOf(Map.class, config.get("server"));
        Map<?, ?> features = assertInstanceOf(Map.class, server.get("features"));
        assertEquals(true, features.get("enabled"));
        assertEquals(List.of("first", "second"), features.get("labels"));
    }

    private static SysParamsDTO parameter(String code, String value, String type) {
        SysParamsDTO parameter = new SysParamsDTO();
        parameter.setParamCode(code);
        parameter.setParamValue(value);
        parameter.setValueType(type);
        return parameter;
    }

    private static ConfigServiceImpl newService(SysParamsService sysParamsService, RedisUtils redisUtils) {
        return new ConfigServiceImpl(
                sysParamsService,
                mock(DeviceService.class),
                mock(ModelConfigService.class),
                mock(AgentService.class),
                mock(AgentTemplateService.class),
                redisUtils,
                mock(TimbreService.class),
                mock(AgentPluginMappingService.class),
                mock(AgentMcpAccessPointService.class),
                mock(AgentContextProviderService.class),
                mock(VoiceCloneService.class),
                mock(AgentVoicePrintDao.class),
                mock(CorrectWordFileService.class));
    }
}
