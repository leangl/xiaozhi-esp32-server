package xiaozhi.modules.agent.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import java.net.URI;
import org.junit.jupiter.api.*;
import org.mockito.MockedStatic;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.client.RestTemplate;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.IdentifyVoicePrintResponse;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.entity.AgentVoicePrintEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.sys.service.SysParamsService;

class AgentVoicePrintOptionalBoundaryTest {
    private MockedStatic<MessageUtils> messages;
    @BeforeEach void setup() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt())).thenReturn("Voiceprint service unavailable");
    }
    @AfterEach void cleanup() { messages.close(); }

    @Test
    void rejectedStoredEndpointIsUnavailableBeforeAudioAndTransactionSideEffects() {
        var params = mock(SysParamsService.class);
        var audio = mock(AgentChatAudioService.class);
        var history = mock(AgentChatHistoryService.class);
        var transaction = mock(TransactionTemplate.class);
        var http = mock(RestTemplate.class);
        when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn("https://unknown.example/health?key=synthetic-secret");
        var service = new AgentVoicePrintServiceImpl(audio, http, params, history, transaction, Runnable::run);
        var error = assertThrows(RenException.class, () -> service.insert(new AgentVoicePrintSaveDTO()));
        assertFalse(error.getMessage().contains("synthetic-secret"));
        verifyNoInteractions(audio, history, transaction, http);
        assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(service, "cancelVoicePrint", "synthetic-id"));
        verifyNoInteractions(http);
    }

    @Test
    void loopbackRegistrationAndDeletionKeepBearerKeysOutOfTheDestination() {
        var params = mock(SysParamsService.class);
        when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn("http://127.0.0.1:8181/health?key=synthetic%2Bkey&status=yes");
        var http = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(http).build();
        server.expect(requestTo("http://127.0.0.1:8181/voiceprint/register"))
                .andExpect(method(HttpMethod.POST)).andExpect(header("Authorization", "Bearer synthetic+key"))
                .andRespond(withSuccess("true", MediaType.APPLICATION_JSON));
        server.expect(requestTo("http://127.0.0.1:8181/voiceprint/synthetic-id"))
                .andExpect(method(HttpMethod.DELETE)).andExpect(header("Authorization", "Bearer synthetic+key"))
                .andRespond(withSuccess("true", MediaType.APPLICATION_JSON));
        var service = service(params, http);
        var resource = new ByteArrayResource(new byte[]{1, 2, 3}) {
            @Override public String getFilename() { return "synthetic.wav"; }
        };
        ReflectionTestUtils.invokeMethod(service, "registerVoicePrint", "synthetic-id", resource);
        ReflectionTestUtils.invokeMethod(service, "cancelVoicePrint", "synthetic-id");
        server.verify();
    }

    @Test
    void redirectsAndErrorsNeverExposeCredentialsOrResponseBodies() {
        var params = mock(SysParamsService.class);
        when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn("http://localhost:8181/health?key=synthetic-secret");
        var http = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(http).build();
        server.expect(requestTo("http://localhost:8181/voiceprint/synthetic-id"))
                .andRespond(withStatus(HttpStatus.TEMPORARY_REDIRECT).location(URI.create("https://unknown.example/collect")));
        server.expect(requestTo("http://localhost:8181/voiceprint/synthetic-id"))
                .andRespond(withServerError().body("synthetic-secret private-audio"));
        var service = service(params, http);
        for (int i = 0; i < 2; i++) {
            var error = assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(service, "cancelVoicePrint", "synthetic-id"));
            assertFalse(error.getMessage().contains("synthetic-secret"));
            assertFalse(error.getMessage().contains("private-audio"));
            assertNull(error.getCause());
        }
        server.verify();
    }

    @Test
    void malformedOrMissingKeysFailWithExistingRedactedEnvelope() {
        var params = mock(SysParamsService.class);
        var http = mock(RestTemplate.class);
        var service = service(params, http);
        for (String url : new String[]{"http://localhost/health", "http://localhost/health?key=", "http://localhost/health?key=a&key=b", "http://localhost/health?key=%zz"}) {
            when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn(url);
            assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(service, "cancelVoicePrint", "synthetic-id"));
        }
        verifyNoInteractions(http);
    }

    @Test
    void recognitionUsesTheSameGuardBeforeSendingAudioAndSpeakerIds() {
        com.baomidou.mybatisplus.core.metadata.TableInfoHelper.initTableInfo(
                new org.apache.ibatis.builder.MapperBuilderAssistant(
                        new com.baomidou.mybatisplus.core.MybatisConfiguration(), "optional-voiceprint-fixture"),
                AgentVoicePrintEntity.class);
        var params = mock(SysParamsService.class);
        var http = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(http).build();
        var service = service(params, http);
        var dao = mock(AgentVoicePrintDao.class);
        ReflectionTestUtils.setField(service, "baseMapper", dao);
        var speaker = new AgentVoicePrintEntity();
        speaker.setId("synthetic-speaker");
        when(dao.selectList(any())).thenReturn(java.util.List.of(speaker));
        when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn("https://unknown.example/health?key=synthetic-secret");
        assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(service,
                "identifyVoicePrint", "synthetic-agent", new ByteArrayResource(new byte[]{1, 2, 3})));
        when(params.getValue(Constant.SERVER_VOICE_PRINT, true)).thenReturn("http://localhost:8181/health?key=synthetic-key");
        server.expect(requestTo("http://localhost:8181/voiceprint/identify"))
                .andExpect(method(HttpMethod.POST)).andExpect(header("Authorization", "Bearer synthetic-key"))
                .andRespond(withSuccess("{\"speaker_id\":\"synthetic-speaker\",\"score\":0.9}", MediaType.APPLICATION_JSON));
        IdentifyVoicePrintResponse result = ReflectionTestUtils.invokeMethod(service,
                "identifyVoicePrint", "synthetic-agent", new ByteArrayResource(new byte[]{1, 2, 3}));
        assertEquals("synthetic-speaker", result.getSpeakerId());
        assertEquals(0.9, result.getScore());
        server.verify();
    }

    private AgentVoicePrintServiceImpl service(SysParamsService params, RestTemplate http) {
        return new AgentVoicePrintServiceImpl(mock(AgentChatAudioService.class), http, params,
                mock(AgentChatHistoryService.class), mock(TransactionTemplate.class), Runnable::run);
    }
}
