package xiaozhi.modules.sys.controller;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import java.net.URI;
import org.junit.jupiter.api.*;
import org.mockito.MockedStatic;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;

class SysParamsOptionalBoundaryTest {
    private MockedStatic<MessageUtils> messages;
    @BeforeEach void setup() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt())).thenReturn("Service validation failed");
    }
    @AfterEach void cleanup() { messages.close(); }

    @Test
    void rejectedStatusTargetsNeverReachTransportOrMutateSavedParameters() {
        var params = mock(SysParamsService.class);
        var config = mock(ConfigService.class);
        var http = mock(RestTemplate.class);
        var controller = new SysParamsController(params, config, http);
        for (String code : new String[]{Constant.SERVER_OTA, Constant.SERVER_MCP_ENDPOINT, Constant.SERVER_VOICE_PRINT}) {
            var dto = new SysParamsDTO();
            dto.setParamCode(code);
            dto.setParamValue("https://api.openai.com/ota/?key=synthetic-secret");
            if (code.equals(Constant.SERVER_OTA)) dto.setParamValue("https://api.openai.com/ota/");
            dto.setValueType("string");
            var create = assertThrows(RenException.class, () -> controller.save(dto));
            assertFalse(create.getMessage().contains("synthetic-secret"));
            dto.setId(1L);
            assertThrows(RenException.class, () -> controller.update(dto));
        }
        verifyNoInteractions(params, config, http);
    }

    @Test
    void rejectedWebsocketStatusDoesNotUseTheUnboundedLegacyHelper() {
        var controller = new SysParamsController(mock(SysParamsService.class), mock(ConfigService.class), mock(RestTemplate.class));
        var error = assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(controller,
                "validateWebSocketUrls", Constant.SERVER_WEBSOCKET, "wss://unknown.example/xiaozhi/v1/"));
        assertFalse(error.getMessage().contains("unknown.example"));
    }

    @Test
    void reviewedLoopbackStatusEndpointsAreUsableWithExactRoles() {
        var template = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(template).build();
        server.expect(requestTo("http://127.0.0.1:8181/ota/")).andRespond(withSuccess("OTA", MediaType.TEXT_PLAIN));
        server.expect(requestTo("http://127.0.0.1:8181/mcp?key=synthetic")).andRespond(withSuccess("success", MediaType.TEXT_PLAIN));
        server.expect(requestTo("http://127.0.0.1:8181/health?key=synthetic")).andRespond(withSuccess("healthy", MediaType.TEXT_PLAIN));
        var controller = new SysParamsController(mock(SysParamsService.class), mock(ConfigService.class), template);
        ReflectionTestUtils.invokeMethod(controller, "validateOtaUrl", Constant.SERVER_OTA, "http://127.0.0.1:8181/ota/");
        ReflectionTestUtils.invokeMethod(controller, "validateMcpUrl", Constant.SERVER_MCP_ENDPOINT, "http://127.0.0.1:8181/mcp?key=synthetic");
        ReflectionTestUtils.invokeMethod(controller, "validateVoicePrint", Constant.SERVER_VOICE_PRINT, "http://127.0.0.1:8181/health?key=synthetic");
        server.verify();
    }

    @Test
    void statusRedirectsDoNotForwardKeysOrLeakRemoteBodies() {
        var template = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(template).build();
        server.expect(requestTo("http://localhost:8181/health?key=synthetic-secret"))
                .andRespond(withStatus(HttpStatus.TEMPORARY_REDIRECT).location(URI.create("https://unknown.example/trap"))
                        .body("synthetic-secret"));
        var controller = new SysParamsController(mock(SysParamsService.class), mock(ConfigService.class), template);
        var error = assertThrows(RenException.class, () -> ReflectionTestUtils.invokeMethod(controller,
                "validateVoicePrint", Constant.SERVER_VOICE_PRINT, "http://localhost:8181/health?key=synthetic-secret"));
        assertFalse(error.getMessage().contains("synthetic-secret"));
        server.verify();
    }
}
