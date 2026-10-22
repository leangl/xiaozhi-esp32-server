package xiaozhi.modules.knowledge.rag;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.MockedStatic;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestTemplate;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.MessageUtils;

class RAGFlowOptionalBoundaryTest {
    private MockedStatic<MessageUtils> messages;
    @BeforeEach void setup() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt(), any(String[].class)))
                .thenAnswer(invocation -> "RAG unavailable: " + invocation.getArgument(1));
    }
    @AfterEach void cleanup() { messages.close(); }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {"https://api.deepseek.com?key=synthetic-secret", "https://api.openai.com/v1",
            "https://unknown.example/v1", "http://192.168.1.2/rag", "http://127.1/rag",
            "http://user:synthetic-secret@localhost/rag", "http://localhost/rag?key=synthetic-secret"})
    void rejectsUnreviewedRagOriginsBeforeTransportCreation(String url) {
        var error = assertThrows(RenException.class, () -> new RAGFlowClient(url, "synthetic-key"));
        assertFalse(error.getMessage().contains("synthetic-secret"));
        assertFalse(error.getMessage().contains("unknown.example"));
    }

    @Test
    void allRequestKindsUseTheGuardedLoopbackTransport() {
        var client = new RAGFlowClient("http://127.0.0.1:8181/api/v1/", "synthetic-key");
        var template = (RestTemplate) ReflectionTestUtils.getField(client, "restTemplate");
        var server = MockRestServiceServer.bindTo(template).build();
        for (var method : new HttpMethod[]{HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE, HttpMethod.POST}) {
            server.expect(requestTo("http://127.0.0.1:8181/api/v1/items")).andExpect(method(method))
                    .andExpect(header("Authorization", "Bearer synthetic-key"))
                    .andRespond(withSuccess("{\"code\":0,\"data\":[]}", MediaType.APPLICATION_JSON));
        }
        client.get("items", null);
        client.post("/items", Map.of("question", "synthetic"));
        client.put("items", Map.of());
        client.delete("items", Map.of());
        var parts = new LinkedMultiValueMap<String, Object>();
        parts.add("file", "synthetic-file");
        client.postMultipart("items", parts);
        server.verify();
    }

    @Test
    void streamingAndBusinessErrorsDoNotEchoRemoteMessages() {
        var client = new RAGFlowClient("http://localhost:8181", "synthetic-key");
        var server = MockRestServiceServer.bindTo((RestTemplate) ReflectionTestUtils.getField(client, "restTemplate")).build();
        server.expect(requestTo("http://localhost:8181/stream")).andRespond(withSuccess("data: one\n\ndata: two\n", MediaType.TEXT_EVENT_STREAM));
        server.expect(requestTo("http://localhost:8181/fail")).andRespond(withSuccess(
                "{\"code\":5,\"message\":\"synthetic-secret private-body\"}", MediaType.APPLICATION_JSON));
        var lines = new ArrayList<String>();
        client.postStream("stream", Map.of(), lines::add);
        assertEquals(java.util.List.of("data: one", "data: two"), lines);
        var error = assertThrows(RenException.class, () -> client.post("fail", Map.of()));
        assertFalse(error.getMessage().contains("synthetic-secret"));
        server.verify();
    }

    @Test
    void absoluteAndAuthorityPathsCannotSwitchRecipients() {
        var client = new RAGFlowClient("http://localhost:8181", "synthetic-key");
        for (String endpoint : new String[]{"https://unknown.example/receive", "//unknown.example/receive", "items?token=synthetic-secret", "items#secret"}) {
            assertThrows(RenException.class, () -> client.get(endpoint, null));
            assertThrows(RenException.class, () -> client.postStream(endpoint, Map.of(), ignored -> fail("No stream expected")));
        }
    }

    @Test
    void realLoopbackRedirectsNeverReachTheSecondRecipientForJsonOrStream() throws Exception {
        var fixture = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        var requests = new AtomicInteger();
        var redirected = new AtomicInteger();
        String base = "http://127.0.0.1:" + fixture.getAddress().getPort();
        fixture.createContext("/start", exchange -> {
            requests.incrementAndGet();
            exchange.getRequestBody().readAllBytes();
            exchange.getResponseHeaders().set("Location", base + "/trap");
            exchange.sendResponseHeaders(307, -1);
            exchange.close();
        });
        fixture.createContext("/trap", exchange -> { redirected.incrementAndGet(); exchange.close(); });
        fixture.start();
        try {
            var client = new RAGFlowClient(base, "synthetic-key");
            assertThrows(RenException.class, () -> client.post("start", Map.of("private", "synthetic")));
            assertThrows(RenException.class, () -> client.postStream("start", Map.of(), ignored -> fail("No data expected")));
            assertEquals(2, requests.get());
            assertEquals(0, redirected.get());
        } finally { fixture.stop(0); }
    }
}
