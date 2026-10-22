package xiaozhi.common.utils;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;
import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;

class ApprovedProviderCatalogTest {
    @Test
    void deviceVadNeedsNoModelOrEndpointAndDoesNotChangeSilero() {
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("VAD", "device", Map.of("type", "device")));
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("VAD", "device",
                Map.of("type", "device", "max_audio_duration_ms", "60000")));
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("VAD", "silero", Map.of("type", "silero")));
        ModelConfigEntity model = model("VAD", "device", null, null);
        assertTrue(ApprovedProviderCatalog.isAvailable(model));
        AgentUpdateDTO dto = new AgentUpdateDTO();
        dto.setVadModelId(model.getId());
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validateSelections(dto, id -> model));
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validateRuntimeConfig(
                Map.of("VAD", Map.of("DeviceVAD", Map.of("type", "device")))));
    }

    @Test
    void deviceVadDurationIsBoundedAndRedactedForApiAndUiValues() {
        for (Object duration : List.of(1000, 300000, "120000")) {
            assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("VAD", "device",
                    Map.of("type", "device", "max_audio_duration_ms", duration)));
        }
        for (Object duration : List.of(true, false, 0, 999, 300001, 1000.5, "1000.0", "private-value", Map.of(), List.of())) {
            RenException error = assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("VAD", "device",
                    Map.of("type", "device", "max_audio_duration_ms", duration)));
            assertFalse(error.getMessage().contains("private-value"));
        }
        Map<String, Object> nullValue = new java.util.HashMap<>();
        nullValue.put("type", "device");
        nullValue.put("max_audio_duration_ms", null);
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("VAD", "device", nullValue));
    }

    @ParameterizedTest
    @CsvSource({"ASR,openai,base_url", "LLM,openai,base_url", "VLLM,openai,base_url", "TTS,openai,api_url", "RAG,ragflow,base_url"})
    void supportsReviewedActualEndpointsRegardlessOfAlias(String role, String type, String key) {
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate(role, type,
                Map.of("type", type, key, "http://127.0.0.1:9999/v1", "model_name", "arbitrary-legacy-name")));
    }

    @ParameterizedTest
    @ValueSource(strings = {"OpenAI", "OPENAI", "openai ", " openai"})
    void noncanonicalImplementationTypesAreRejectedWithoutRewritingLegacyRecords(String type) {
        ModelConfigEntity legacy = model("LLM", type, "base_url", "https://api.openai.com/v1");
        RenException rejected = assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate(
                "llm", "OPENAI", legacy.getConfigJson()));
        assertTrue(rejected.getMessage().startsWith("LLM configuration is unavailable"));
        assertFalse(rejected.getMessage().contains(type));
        assertFalse(ApprovedProviderCatalog.isSupported(legacy));
        assertFalse(ApprovedProviderCatalog.isAvailable(legacy));
        assertEquals(type, legacy.getConfigJson().getStr("type"));
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validateRuntimeConfig(Map.of(
                "LLM", Map.of("legacy", legacy.getConfigJson()))));
    }

    @Test
    void roleAndProviderRouteCodesMayNormalizeButEmittedImplementationCodeIsExact() {
        Map<String, Object> config = Map.of("type", "openai", "base_url", "https://api.openai.com/v1");
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("llM", "OpenAI", config));
        assertEquals("openai", config.get("type"));
    }

    @ParameterizedTest
    @CsvSource({"ASR,fun_local", "LLM,coze", "TTS,edge", "Memory,mem0ai", "Intent,unknown", "VAD,unknown", "LLM,gemini"})
    void unknownAndRemovedImplementationsAreUnavailable(String role, String type) {
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate(role, type,
                Map.of("type", type, "base_url", "https://api.openai.com/v1")));
    }

    @Test
    void endpointsAndProxyAliasesFailClosedAndRedacted() {
        for (Map<String, Object> config : List.of(
                Map.<String, Object>of("type", "openai", "base_url", "https://user:secret@unreviewed.example/v1"),
                Map.<String, Object>of("type", "openai", "base_url", "https://api.openai.com/v1", "api_url", "https://unreviewed.example/key-secret"),
                Map.<String, Object>of("type", "openai", "base_url", "https://api.openai.com/v1", "http_proxy", "secret-proxy"))) {
            RenException error = assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("LLM", "openai", config));
            assertTrue(error.getMessage().startsWith("LLM configuration is unavailable"));
            assertFalse(error.getMessage().contains("secret"));
            assertFalse(error.getMessage().contains("example"));
            assertNull(error.getCause());
        }
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("LLM", "ollama",
                Map.of("type", "ollama", "base_url", "https://api.openai.com/v1")));
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("RAG", "ragflow",
                Map.of("type", "ragflow", "base_url", "https://api.openai.com/v1")));
    }

    @Test
    void migrationPredicateDoesNotDependOnEnabledFlagOrModelId() {
        ModelConfigEntity model = model("LLM", "openai", "base_url", "https://api.openai.com/v1");
        model.setId("LLM_AliyunCompatibleAlias");
        model.setIsEnabled(0);
        assertTrue(ApprovedProviderCatalog.isSupported(model));
        assertFalse(ApprovedProviderCatalog.isAvailable(model));
        model.setIsEnabled(1);
        assertTrue(ApprovedProviderCatalog.isAvailable(model));
    }

    @Test
    void suppliedSelectionRejectsRoleConfusionAndStaleAuxiliaryLlm() {
        AgentUpdateDTO dto = new AgentUpdateDTO();
        dto.setTtsModelId("id");
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validateSelections(dto,
                id -> model("LLM", "openai", "base_url", "http://localhost:9999")));
        dto.setTtsModelId(null);
        dto.setIntentModelId("intent");
        ModelConfigEntity intent = model("Intent", "intent_llm", null, null);
        intent.getConfigJson().set("llm", "legacy");
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validateSelections(dto,
                id -> id.equals("intent") ? intent : model("LLM", "coze", null, null)));
    }

    @Test
    void cachedRuntimeBranchesAndIntentFunctionsAreRevalidated() {
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validateRuntimeConfig(Map.of(
                "ASR", Map.of("alias", Map.of("type", "openai", "base_url", "https://unknown.example")))));
        assertDoesNotThrow(() -> ApprovedProviderCatalog.validate("Intent", "function_call",
                Map.of("type", "function_call", "functions", new String[] {"get_lunar", "hass_get_state"})));
        assertThrows(RenException.class, () -> ApprovedProviderCatalog.validate("Intent", "function_call",
                Map.of("type", "function_call", "functions", "get_weather;web_search")));
        assertTrue(ApprovedProviderCatalog.isSupportedPlugin("search_from_ragflow"));
        assertFalse(ApprovedProviderCatalog.isSupportedPlugin("get_news_from_newsnow"));
    }

    public static ModelConfigEntity model(String role, String type, String endpointKey, String endpoint) {
        ModelConfigEntity model = new ModelConfigEntity();
        model.setId("synthetic-model");
        model.setModelType(role);
        model.setIsEnabled(1);
        model.setIsDefault(0);
        JSONObject config = new JSONObject().set("type", type).set("api_key", "synthetic-secret");
        if (endpointKey != null) config.set(endpointKey, endpoint);
        model.setConfigJson(config);
        return model;
    }
}
