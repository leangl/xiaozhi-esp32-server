package xiaozhi.modules.sys.utils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.Base64;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.slf4j.LoggerFactory;
import xiaozhi.common.config.RestTemplateConfig;

class WebSocketValidatorOptionalBoundaryTest {
    private ListAppender<ILoggingEvent> logs;
    private Logger logger;
    @BeforeEach void captureLogs() {
        logs = new ListAppender<>();
        logs.start();
        logger = (Logger) LoggerFactory.getLogger(WebSocketValidator.class);
        logger.addAppender(logs);
    }
    @AfterEach void releaseLogs() { logger.detachAppender(logs); logs.stop(); }

    @Test
    void pureFormatHelperRetainsItsExistingMeaningWithoutMakingRequests() {
        assertTrue(WebSocketValidator.validateUrlFormat("wss://unknown.example/xiaozhi/v1/"));
        assertTrue(WebSocketValidator.validateUrlFormat("ws://127.0.0.1:8181/socket"));
        assertFalse(WebSocketValidator.validateUrlFormat("https://localhost/socket"));
        assertFalse(WebSocketValidator.validateUrlFormat("ws://localhost/socket?token=synthetic-secret"));
        assertFalse(WebSocketValidator.validateUrlFormat(null));
    }

    @ParameterizedTest
    @ValueSource(strings = {"wss://unknown.example/socket", "wss://api.openai.com/socket", "ws://192.168.1.2/socket",
            "ws://169.254.169.254/socket", "ws://127.1/socket", "ws://localhost.evil.example/socket"})
    void directInvocationRejectsUnreviewedTargetsBeforeCreatingTransport(String url) {
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            assertFalse(WebSocketValidator.testConnection(url));
            transport.verifyNoInteractions();
            assertLogsAreRedacted();
        }
    }

    @Test
    void directInvocationAcceptsAnActualReviewedLoopbackHandshake() throws Exception {
        try (var server = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"));
                var executor = Executors.newSingleThreadExecutor()) {
            server.setSoTimeout(5000);
            var fixture = executor.submit(() -> {
                try (var socket = server.accept()) {
                    socket.setSoTimeout(5000);
                    var bytes = new java.io.ByteArrayOutputStream();
                    String headers;
                    do {
                        int value = socket.getInputStream().read();
                        if (value < 0 || bytes.size() >= 16_384) throw new java.io.IOException("Invalid fixture handshake");
                        bytes.write(value);
                        headers = bytes.toString(StandardCharsets.US_ASCII);
                    } while (!headers.endsWith("\r\n\r\n"));
                    assertTrue(headers.startsWith("GET /socket HTTP/1.1"));
                    String key = headers.lines().filter(line -> line.toLowerCase().startsWith("sec-websocket-key:"))
                            .findFirst().orElseThrow().split(":", 2)[1].trim();
                    String accept = Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1")
                            .digest((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").getBytes(StandardCharsets.US_ASCII)));
                    socket.getOutputStream().write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "
                            + accept + "\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                    socket.getOutputStream().flush();
                    return true;
                }
            });
            assertTrue(WebSocketValidator.testConnection("ws://127.0.0.1:" + server.getLocalPort() + "/socket"));
            assertTrue(fixture.get(5, TimeUnit.SECONDS));
        }
    }

    @ParameterizedTest
    @ValueSource(ints = {301, 302, 303, 307, 308})
    void directInvocationNeverFollowsRedirectsOrLogsResponseBodies(int status) throws Exception {
        var fixture = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        var requests = new AtomicInteger();
        var redirected = new AtomicInteger();
        String base = "http://127.0.0.1:" + fixture.getAddress().getPort();
        fixture.createContext("/socket", exchange -> {
            requests.incrementAndGet();
            exchange.getResponseHeaders().set("Location", base + "/trap?token=synthetic-secret");
            byte[] body = "synthetic-secret raw-response-body https://unknown.example/private".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(status, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        fixture.createContext("/trap", exchange -> { redirected.incrementAndGet(); exchange.close(); });
        fixture.start();
        try {
            assertFalse(WebSocketValidator.testConnection("ws://127.0.0.1:" + fixture.getAddress().getPort() + "/socket"));
            assertEquals(1, requests.get());
            assertEquals(0, redirected.get());
            assertLogsAreRedacted();
        } finally { fixture.stop(0); }
    }

    @Test
    void failedHandshakeUsesBoundedTransportAndDoesNotLogExceptionChains() {
        var client = mock(HttpClient.class);
        var builder = mock(WebSocket.Builder.class);
        when(client.newWebSocketBuilder()).thenReturn(builder);
        when(builder.connectTimeout(Duration.ofSeconds(5))).thenReturn(builder);
        when(builder.buildAsync(any(URI.class), any(WebSocket.Listener.class)))
                .thenReturn(CompletableFuture.failedFuture(new IllegalStateException(
                        "synthetic-secret raw-response-body https://unknown.example/private")));
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            transport.when(() -> RestTemplateConfig.directHttpClient(Duration.ofSeconds(5))).thenReturn(client);
            assertFalse(WebSocketValidator.testConnection("ws://localhost:8181/socket"));
            verify(client).shutdownNow();
            verify(builder).connectTimeout(Duration.ofSeconds(5));
            assertLogsAreRedacted();
        }
    }

    private void assertLogsAreRedacted() {
        assertFalse(logs.list.isEmpty());
        for (var event : logs.list) {
            assertFalse(event.getFormattedMessage().contains("synthetic-secret"));
            assertFalse(event.getFormattedMessage().contains("raw-response-body"));
            assertFalse(event.getFormattedMessage().contains("unknown.example"));
            assertNull(event.getThrowableProxy());
        }
    }
}
