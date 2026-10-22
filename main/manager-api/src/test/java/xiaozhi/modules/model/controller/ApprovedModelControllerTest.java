package xiaozhi.modules.model.controller;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.model.service.ModelProviderService;
import xiaozhi.modules.timbre.service.TimbreService;

class ApprovedModelControllerTest {
    private final ModelConfigService models = mock(ModelConfigService.class);
    private final TimbreService voices = mock(TimbreService.class);
    private final AgentTemplateService templates = mock(AgentTemplateService.class);
    private final ModelController controller = new ModelController(mock(ModelProviderService.class), voices, models,
            mock(ConfigService.class), templates);

    @Test
    void settingLegacyDefaultOrEnablingItCannotClearWorkingDefaultsFirst() {
        ModelConfigEntity legacy = new ModelConfigEntity();
        legacy.setModelType("TTS");
        legacy.setConfigJson(new JSONObject().set("type", "edge"));
        when(models.selectById("legacy")).thenReturn(legacy);
        assertThrows(RenException.class, () -> controller.setDefaultModel("legacy"));
        assertThrows(RenException.class, () -> controller.enableModelConfig("legacy", 1));
        verify(models, never()).setDefaultModel(anyString(), anyInt());
        verify(models, never()).updateById(any());
        verifyNoInteractions(templates);
    }

    @Test
    void ordinaryVoiceSelectorOmitsClonesAndUnreviewedPreviewUrlsWithoutChangingStoredRows() {
        VoiceDTO normal = new VoiceDTO("voice", "synthetic voice", "https://unknown.example/demo?api_key=secret");
        VoiceDTO clone = new VoiceDTO("clone", "historical clone");
        clone.setIsClone(true);
        when(voices.getVoiceNames("approved", null)).thenReturn(List.of(normal, clone));
        var result = controller.getVoiceList("approved", null);
        assertEquals(0, result.getCode());
        assertEquals(1, result.getData().size());
        assertNull(result.getData().get(0).getVoiceDemo());
        assertEquals("voice", result.getData().get(0).getId());
        assertTrue(normal.getVoiceDemo().contains("secret"));
        verify(models).requireSelectable("approved", "tts");
    }
}
