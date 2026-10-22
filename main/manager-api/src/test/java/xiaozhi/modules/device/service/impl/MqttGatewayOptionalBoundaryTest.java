package xiaozhi.modules.device.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.ProxySelector;
import java.net.SocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;
import xiaozhi.common.config.RestTemplateConfig;

class MqttGatewayOptionalBoundaryTest {
    private static final Instant NOW = Instant.parse("2026-07-14T00:30:00Z");
    private static final String KEY = "synthetic-signature-key";
    private static final String PRIVATE = "synthetic-secret raw-response-body https://unknown.example/private";

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {"https://unknown.example/mqtt?key=synthetic-secret", "https://api.openai.com/mqtt",
            "https://generativelanguage.googleapis.com/mqtt", "http://192.168.1.2/mqtt", "http://169.254.169.254/mqtt",
            "http://127.1/mqtt", "http://127.0.0.1.evil.example/mqtt", "http://user:synthetic-secret@localhost/mqtt",
            "http://localhost/mqtt#synthetic-secret", "file:///private/data", "ws://localhost/mqtt"})
    void rejectedTargetsFailBeforeTransportAndCredentialGeneration(String url) {
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            // A null clock also proves rejection precedes the date-based token calculation.
            var error = assertThrows(MqttGatewayAuthorization.GatewayRequestException.class,
                    () -> MqttGatewayAuthorization.postJson(url, PRIVATE, KEY, null));
            assertNull(error.statusCode());
            assertRedacted(error);
            transport.verifyNoInteractions();
        }
    }

    @ParameterizedTest
    @ValueSource(ints = {0, -1, 30001})
    void unboundedTimeoutsAreRejectedBeforeTransport(int timeout) {
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            assertThrows(MqttGatewayAuthorization.GatewayRequestException.class,
                    () -> MqttGatewayAuthorization.postJson("http://localhost:8181/mqtt", "{}", KEY, NOW, timeout));
            transport.verifyNoInteractions();
        }
    }

    @Test
    void actualJsonAndSha256BearerContractIsUnchangedAndDoesNotUseTheDefaultProxy() throws Exception {
        var fixture = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        var requests = new AtomicInteger();
        var proxyCalls = new AtomicInteger();
        String requestBody = "{\"clientIds\":[\"synthetic-device\"],\"text\":\"hello 小智\"}";
        String expectedToken = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(("2026-07-14" + KEY).getBytes(StandardCharsets.UTF_8)));
        fixture.createContext("/mqtt", exchange -> {
            requests.incrementAndGet();
            boolean contractMatches = "POST".equals(exchange.getRequestMethod())
                    && "application/json".equals(exchange.getRequestHeaders().getFirst("Content-Type"))
                    && ("Bearer " + expectedToken).equals(exchange.getRequestHeaders().getFirst("Authorization"))
                    && requestBody.equals(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            byte[] body = (contractMatches ? "{\"online\":true}" : "{\"contract\":false}").getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(contractMatches ? 200 : 400, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        ProxySelector previous = ProxySelector.getDefault();
        ProxySelector.setDefault(new ProxySelector() {
            @Override public List<Proxy> select(URI uri) {
                if ("127.0.0.1".equals(uri.getHost()) && uri.getPort() == fixture.getAddress().getPort()) {
                    proxyCalls.incrementAndGet();
                    throw new AssertionError("Gateway fixture must not use the default proxy");
                }
                return previous == null ? List.of(Proxy.NO_PROXY) : previous.select(uri);
            }
            @Override public void connectFailed(URI uri, SocketAddress address, IOException error) {}
        });
        fixture.start();
        try {
            assertEquals("{\"online\":true}", MqttGatewayAuthorization.postJson(
                    "http://127.0.0.1:" + fixture.getAddress().getPort() + "/mqtt", requestBody, KEY, NOW));
            assertEquals(1, requests.get());
            assertEquals(0, proxyCalls.get());
        } finally { fixture.stop(0); ProxySelector.setDefault(previous); }
    }

    @ParameterizedTest
    @ValueSource(ints = {301, 302, 303, 307, 308})
    void redirectNeverForwardsJsonOrAuthorizationAndIsNotRetried(int status) throws Exception {
        var fixture = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        var requests = new AtomicInteger();
        var redirected = new AtomicInteger();
        String base = "http://127.0.0.1:" + fixture.getAddress().getPort();
        fixture.createContext("/mqtt", exchange -> {
            requests.incrementAndGet();
            exchange.getRequestBody().readAllBytes();
            exchange.getResponseHeaders().set("Location", base + "/trap?key=synthetic-secret");
            byte[] body = PRIVATE.getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(status, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        fixture.createContext("/trap", exchange -> { redirected.incrementAndGet(); exchange.close(); });
        fixture.start();
        try {
            var error = assertThrows(MqttGatewayAuthorization.GatewayRequestException.class,
                    () -> MqttGatewayAuthorization.postJson(base + "/mqtt", PRIVATE, KEY, NOW));
            assertEquals(status, error.statusCode());
            assertEquals(1, requests.get());
            assertEquals(0, redirected.get());
            assertRedacted(error);
        } finally { fixture.stop(0); }
    }

    @Test
    void transportFailureCannotExposeTheRequestOrExceptionChain() throws Exception {
        var client = mock(HttpClient.class);
        when(client.send(any(HttpRequest.class), org.mockito.ArgumentMatchers.<HttpResponse.BodyHandler<String>>any()))
                .thenThrow(new IOException(PRIVATE));
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            transport.when(() -> RestTemplateConfig.directHttpClient(Duration.ofSeconds(10))).thenReturn(client);
            var error = assertThrows(MqttGatewayAuthorization.GatewayRequestException.class,
                    () -> MqttGatewayAuthorization.postJson("http://localhost:8181/mqtt", PRIVATE, KEY, NOW));
            assertRedacted(error);
            verify(client).shutdownNow();
        }
    }

    @Test
    void interruptedRequestRestoresTheInterruptFlagWithoutExposingTheCause() throws Exception {
        var client = mock(HttpClient.class);
        when(client.send(any(HttpRequest.class), org.mockito.ArgumentMatchers.<HttpResponse.BodyHandler<String>>any()))
                .thenThrow(new InterruptedException(PRIVATE));
        try (var transport = mockStatic(RestTemplateConfig.class)) {
            transport.when(() -> RestTemplateConfig.directHttpClient(Duration.ofSeconds(10))).thenReturn(client);
            var error = assertThrows(MqttGatewayAuthorization.GatewayRequestException.class,
                    () -> MqttGatewayAuthorization.postJson("http://localhost:8181/mqtt", PRIVATE, KEY, NOW));
            assertTrue(Thread.currentThread().isInterrupted());
            assertRedacted(error);
            verify(client).shutdownNow();
        } finally { Thread.interrupted(); }
    }

    private void assertRedacted(Throwable error) {
        assertFalse(error.getMessage().contains("synthetic-secret"));
        assertFalse(error.getMessage().contains("raw-response-body"));
        assertFalse(error.getMessage().contains("unknown.example"));
        assertFalse(error.getMessage().contains(KEY));
        assertNull(error.getCause());
    }
}
