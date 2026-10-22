package xiaozhi.modules.voiceclone.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.*;
import org.mockito.MockedStatic;
import org.springframework.test.util.ReflectionTestUtils;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.sys.dao.SysUserDao;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.voiceclone.dao.VoiceCloneDao;
import xiaozhi.modules.voiceclone.dto.VoiceCloneDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

class VoiceCloneUnavailableBoundaryTest {
    private MockedStatic<MessageUtils> messages;
    @BeforeEach void setup() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt(), any(String[].class)))
                .thenAnswer(invocation -> "Training failed: " + invocation.getArgument(1));
    }
    @AfterEach void cleanup() { messages.close(); }

    @Test
    void newCloningRequestsAreExplicitlyUnavailableWithoutReadingKeysOrCreatingRecords() {
        var models = mock(ModelConfigService.class);
        var dao = mock(VoiceCloneDao.class);
        var service = new VoiceCloneServiceImpl(models, mock(SysUserService.class), mock(SysUserDao.class), new ObjectMapper());
        ReflectionTestUtils.setField(service, "baseDao", dao);
        var error = assertThrows(RenException.class, () -> service.save(new VoiceCloneDTO()));
        assertEquals(ErrorCode.VOICE_CLONE_TRAINING_FAILED, error.getCode());
        assertTrue(error.getMessage().contains("unavailable"));
        verifyNoInteractions(models, dao);
    }

    @Test
    void staleTrainingRequestsPreserveHistoricalAudioProviderIdAndStatus() {
        var models = mock(ModelConfigService.class);
        var dao = mock(VoiceCloneDao.class);
        var service = new VoiceCloneServiceImpl(models, mock(SysUserService.class), mock(SysUserDao.class), new ObjectMapper());
        ReflectionTestUtils.setField(service, "baseDao", dao);
        var entity = new VoiceCloneEntity();
        entity.setId("historical");
        entity.setModelId("legacy-doubao-model");
        entity.setVoiceId("legacy-voice-id");
        entity.setVoice(new byte[]{1, 2, 3});
        entity.setTrainStatus(2);
        when(dao.selectById("historical")).thenReturn(entity);
        var error = assertThrows(RenException.class, () -> service.cloneAudio("historical"));
        assertEquals(ErrorCode.VOICE_CLONE_TRAINING_FAILED, error.getCode());
        assertEquals(2, entity.getTrainStatus());
        assertEquals("legacy-voice-id", entity.getVoiceId());
        assertArrayEquals(new byte[]{1, 2, 3}, service.getVoiceData("historical"));
        verify(dao, times(2)).selectById("historical");
        verifyNoMoreInteractions(dao);
        verifyNoInteractions(models);
    }
}
