package xiaozhi.modules.model.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.util.List;
import org.junit.jupiter.api.Test;
import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.dto.ModelConfigBodyDTO;
import xiaozhi.modules.model.dto.ModelProviderDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelProviderService;
import xiaozhi.modules.timbre.dao.TimbreDao;
import xiaozhi.modules.timbre.entity.TimbreEntity;

class ApprovedModelBoundaryTest {
    private final ModelConfigDao dao = mock(ModelConfigDao.class);
    private final ModelProviderService providers = mock(ModelProviderService.class);
    private final RedisUtils redis = mock(RedisUtils.class);
    private final TimbreDao voices = mock(TimbreDao.class);
    private final ModelConfigServiceImpl service = new ModelConfigServiceImpl(dao, providers, redis, mock(AgentDao.class), voices);

    @Test
    void removedOrMismatchedVoicesCannotBeReusedUnderAnApprovedTtsModel() {
        ModelConfigEntity tts = model("tts", "openai", "http://localhost:9999/v1");
        tts.setModelType("TTS");
        tts.getConfigJson().set("api_url", "http://localhost:9999/v1/audio/speech");
        when(dao.selectById("tts")).thenReturn(tts);
        TimbreEntity staleVoice = new TimbreEntity();
        staleVoice.setTtsModelId("removed-tts");
        when(voices.selectById("stale-voice")).thenReturn(staleVoice);
        assertThrows(RenException.class, () -> service.validateVoiceSelection("tts", "stale-voice"));
        assertThrows(RenException.class, () -> service.validateVoiceSelection("tts", "removed-clone"));
        staleVoice.setTtsModelId("tts");
        assertDoesNotThrow(() -> service.validateVoiceSelection("tts", "stale-voice"));
    }

    @Test
    void rejectedCreateDoesNotInsertOrInvalidateWorkingConfiguration() {
        ModelConfigBodyDTO body = body("openai", "https://user:secret@unreviewed.example/v1");
        when(providers.getList(anyString(), anyString())).thenReturn(List.of(new ModelProviderDTO()));
        RenException error = assertThrows(RenException.class, () -> service.add("LLM", "openai", body));
        assertFalse(error.getMessage().contains("secret"));
        verify(dao, never()).insert(any(ModelConfigEntity.class));
        verifyNoInteractions(redis);
    }

    @Test
    void rejectedEditLeavesPriorConfigAndCacheUnchanged() {
        ModelConfigEntity prior = model("alias", "openai", "http://localhost:9999/v1");
        when(dao.selectById("alias")).thenReturn(prior);
        when(providers.getList(anyString(), anyString())).thenReturn(List.of(new ModelProviderDTO()));
        ModelConfigBodyDTO update = body("openai", "https://unknown.example/v1");
        update.getConfigJson().set("api_key", "***");
        assertThrows(RenException.class, () -> service.edit("LLM", "openai", "alias", update));
        verify(dao, never()).updateById(any(ModelConfigEntity.class));
        verifyNoInteractions(redis);
        assertEquals("http://localhost:9999/v1", prior.getConfigJson().getStr("base_url"));
        assertEquals("synthetic-secret", prior.getConfigJson().getStr("api_key"));
    }

    @Test
    void acceptedAliasUsesEffectiveTypeAndEndpointNotModelName() {
        when(providers.getList(anyString(), anyString())).thenReturn(List.of(new ModelProviderDTO()));
        ModelConfigBodyDTO body = body("openai", "http://127.0.0.1:9999/v1");
        body.setId("LLM_DeepSeekCustomAlias");
        body.setModelName("user supplied model name");
        assertEquals(body.getId(), service.add("LLM", "OPENAI", body).getId());
        verify(dao).insert(argThat((ModelConfigEntity entity) -> body.getId().equals(entity.getId())));
        assertThrows(RenException.class, () -> service.add("LLM", "ollama", body));
    }

    @Test
    void noncanonicalImplementationTypeIsRejectedBeforeCreateOrUpdateMutation() {
        when(providers.getList(anyString(), anyString())).thenReturn(List.of(new ModelProviderDTO()));
        ModelConfigEntity prior = model("alias", "openai", "http://localhost:9999/v1");
        when(dao.selectById("alias")).thenReturn(prior);
        ModelConfigBodyDTO body = body("OpenAI", "http://localhost:9999/v1");
        assertThrows(RenException.class, () -> service.add("LLM", "OPENAI", body));
        assertThrows(RenException.class, () -> service.edit("LLM", "OPENAI", "alias", body));
        verify(dao, never()).insert(any(ModelConfigEntity.class));
        verify(dao, never()).updateById(any(ModelConfigEntity.class));
        verifyNoInteractions(redis);
        assertEquals("openai", prior.getConfigJson().getStr("type"));
        assertEquals("OpenAI", body.getConfigJson().getStr("type"));
    }

    @Test
    void activatingStaleModelViaGenericUpdateIsRejectedBeforeMutation() {
        ModelConfigEntity legacy = model("legacy", "coze", "http://localhost:9999/v1");
        legacy.setIsEnabled(0);
        when(dao.selectById("legacy")).thenReturn(legacy);
        ModelConfigEntity update = new ModelConfigEntity();
        update.setId("legacy");
        update.setIsEnabled(1);
        assertThrows(RenException.class, () -> service.updateById(update));
        verify(dao, never()).updateById(any(ModelConfigEntity.class));
        verifyNoInteractions(redis);
    }

    @Test
    void staleCachedModelsAreRejectedAndValidCacheIsNotMutatedByConsumers() {
        ModelConfigEntity model = model("alias", "openai", "http://localhost:9999/v1");
        when(redis.get(RedisKeys.getModelConfigById("alias"))).thenReturn(model);
        ModelConfigEntity loaded = service.getModelByIdFromCache("alias");
        loaded.getConfigJson().set("private_voice", "test-voice");
        assertFalse(model.getConfigJson().containsKey("private_voice"));
        model.getConfigJson().set("base_url", "https://unknown.example/v1");
        assertThrows(RenException.class, () -> service.getModelByIdFromCache("alias"));
    }

    @Test
    void selectorsFilterLegacyRowsAndReturnOnlyPublicMetadata() {
        ModelConfigEntity approved = model("approved", "openai", "http://localhost:9999/v1");
        ModelConfigEntity aliased = model("blocked", "openai", "https://unknown.example/v1");
        ModelConfigEntity disabled = model("disabled", "openai", "http://localhost:9999/v1");
        disabled.setIsEnabled(0);
        when(dao.selectList(any())).thenReturn(List.of(approved, aliased, disabled));
        var selected = service.getModelCodeList("LLM", null);
        assertEquals(List.of("approved"), selected.stream().map(item -> item.getId()).toList());
        assertFalse(selected.toString().contains("synthetic-secret"));
        assertEquals(1, service.getLlmModelCodeList(null).size());
    }

    @Test
    void legacyManagementReadIsExplicitlyUnavailableAndConfigurationRedacted() {
        ModelConfigEntity legacy = model("legacy", "coze", "https://secret.example/v1");
        when(dao.selectById("legacy")).thenReturn(legacy);
        var result = service.selectById("legacy");
        assertEquals(0, result.getIsEnabled());
        assertEquals(true, result.getConfigJson().getBool("unavailable"));
        assertFalse(result.getConfigJson().toString().contains("secret"));
        assertEquals("synthetic-secret", legacy.getConfigJson().getStr("api_key"));
    }

    @Test
    void batchImportRejectsUnsupportedRowsBeforeWritingAnyRows() {
        assertThrows(RenException.class, () -> service.insertBatch(List.of(
                model("valid", "openai", "http://localhost:9999/v1"),
                model("invalid", "coze", "http://localhost:9999/v1"))));
        verifyNoInteractions(dao, redis);
    }

    @Test
    void cloningSelectorDoesNotPresentOrdinaryTtsAsAReplacementCloningPlatform() {
        assertTrue(service.getTtsPlatformList().isEmpty());
        verifyNoInteractions(dao);
    }

    private ModelConfigBodyDTO body(String type, String url) {
        ModelConfigBodyDTO body = new ModelConfigBodyDTO();
        body.setId("alias");
        body.setIsEnabled(1);
        body.setConfigJson(new JSONObject().set("type", type).set("base_url", url).set("api_key", "synthetic-secret"));
        return body;
    }

    private ModelConfigEntity model(String id, String type, String url) {
        ModelConfigEntity model = new ModelConfigEntity();
        model.setId(id);
        model.setModelName(id);
        model.setModelType("LLM");
        model.setIsEnabled(1);
        model.setConfigJson(body(type, url).getConfigJson());
        return model;
    }
}
