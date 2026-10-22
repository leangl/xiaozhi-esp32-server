package xiaozhi.modules.model.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.user.UserDetail;
import xiaozhi.modules.knowledge.dao.KnowledgeBaseDao;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.dao.ModelProviderDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.entity.ModelProviderEntity;
import xiaozhi.modules.security.user.SecurityUser;

class ApprovedProviderSelectorTest {
    private final ModelProviderDao providers = mock(ModelProviderDao.class);
    private final KnowledgeBaseDao datasets = mock(KnowledgeBaseDao.class);
    private final ModelConfigDao models = mock(ModelConfigDao.class);
    private final ModelProviderServiceImpl service = new ModelProviderServiceImpl(providers, datasets, models);

    @Test
    void pluginSelectorRetainsOwnedEnabledLoopbackKnowledgeAndWithholdsDefaults() {
        ModelProviderEntity music = plugin("play_music");
        music.setFields("[{\"key\":\"api_key\",\"default\":\"platform-secret\"}]");
        when(providers.selectList(any())).thenReturn(List.of(music, plugin("get_weather"), plugin("hass_state")));
        when(datasets.selectList(any())).thenReturn(List.of(dataset("owned", 7L, 1), dataset("other", 8L, 1),
                dataset("disabled", 7L, 0), dataset("blocked", 7L, 1)));
        when(models.selectById("owned-model")).thenReturn(rag("http://127.0.0.1:9999"));
        when(models.selectById("blocked-model")).thenReturn(rag("https://unknown.example"));
        UserDetail user = new UserDetail();
        user.setId(7L);
        try (var security = mockStatic(SecurityUser.class)) {
            security.when(SecurityUser::getUser).thenReturn(user);
            var choices = service.getPluginList();
            assertEquals(List.of("play_music", "hass_state", "ragflow"), choices.stream().map(choice -> choice.getProviderCode()).toList());
            assertFalse(choices.toString().contains("platform-secret"));
            assertFalse(choices.toString().contains("rag-secret"));
            assertEquals("owned", choices.get(2).getId());
        }
        verify(models, never()).selectById("other-model");
        verify(models, never()).selectById("disabled-model");
    }

    @Test
    void selectionsRejectRemovedPluginsOtherUsersAndUnreviewedDestinations() {
        when(providers.selectById("weather")).thenReturn(plugin("get_weather"));
        assertThrows(RenException.class, () -> service.validateSelection("weather", Map.of()));
        when(providers.selectById("hass")).thenReturn(plugin("hass_state"));
        assertThrows(RenException.class, () -> service.validateSelection("hass", Map.of("base_url", "https://unknown.example/secret")));
        assertDoesNotThrow(() -> service.validateSelection("hass", Map.of("base_url", "http://localhost:8123")));
        when(datasets.selectById("other")).thenReturn(dataset("other", 8L, 1));
        UserDetail user = new UserDetail();
        user.setId(7L);
        try (var security = mockStatic(SecurityUser.class)) {
            security.when(SecurityUser::getUser).thenReturn(user);
            assertThrows(RenException.class, () -> service.validateSelection("other", Map.of()));
        }
    }

    private ModelProviderEntity plugin(String code) {
        ModelProviderEntity plugin = new ModelProviderEntity();
        plugin.setProviderCode(code);
        plugin.setModelType("Plugin");
        plugin.setFields("[]");
        return plugin;
    }

    private KnowledgeBaseEntity dataset(String id, Long owner, int status) {
        KnowledgeBaseEntity kb = new KnowledgeBaseEntity();
        kb.setId(id);
        kb.setName(id);
        kb.setCreator(owner);
        kb.setStatus(status);
        kb.setRagModelId(id + "-model");
        return kb;
    }

    private ModelConfigEntity rag(String url) {
        ModelConfigEntity model = new ModelConfigEntity();
        model.setModelType("Rag");
        model.setIsEnabled(1);
        model.setConfigJson(new JSONObject().set("type", "ragflow").set("base_url", url).set("api_key", "rag-secret"));
        return model;
    }
}
