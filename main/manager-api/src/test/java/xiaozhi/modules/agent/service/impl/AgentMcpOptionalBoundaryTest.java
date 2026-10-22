package xiaozhi.modules.agent.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.io.DataInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.ProxySelector;
import java.net.ServerSocket;
import java.net.SocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.core.read.ListAppender;
import ch.qos.logback.classic.spi.ILoggingEvent;
import org.slf4j.LoggerFactory;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.utils.AESUtils;
import xiaozhi.modules.sys.service.SysParamsService;

class AgentMcpOptionalBoundaryTest {
    @Test
    void rejectedStoredEndpointsAreUnavailableBeforeAddressOutputOrNetwork() {
        var params = mock(SysParamsService.class);
        var service = new AgentMcpAccessPointServiceImpl(params);
        for (String url : new String[]{"https://unknown.example/mcp?key=synthetic-secret",
                "https://api.openai.com/mcp?key=synthetic-secret", "http://192.168.1.2/mcp?key=synthetic-secret",
                "http://127.1/mcp?key=synthetic-secret", "http://user:synthetic-secret@localhost/mcp",
                "http://localhost/mcp", "http://localhost/mcp?key=", "http://localhost/mcp?key=a&key=b"}) {
            when(params.getValue(Constant.SERVER_MCP_ENDPOINT, true)).thenReturn(url);
            assertNull(service.getAgentMcpAccessAddress("synthetic-agent"));
            assertEquals(List.of(), service.getAgentMcpToolsList("synthetic-agent"));
        }
    }

    @Test
    void derivedAddressPreservesExistingEncryptedTokenContractWithoutExposingServiceKey() {
        var params = mock(SysParamsService.class);
        when(params.getValue(Constant.SERVER_MCP_ENDPOINT, true))
                .thenReturn("https://localhost:8181/root/mcp?key=synthetic%2Bkey&extra=/not/a/path");
        String address = new AgentMcpAccessPointServiceImpl(params).getAgentMcpAccessAddress("synthetic-agent");
        URI uri = URI.create(address);
        assertEquals("wss", uri.getScheme());
        assertEquals("localhost", uri.getHost());
        assertEquals("/root/mcp/", uri.getPath());
        assertFalse(address.contains("synthetic"));
        assertFalse(address.contains("extra="));
        String token = URLDecoder.decode(uri.getRawQuery().substring("token=".length()), StandardCharsets.UTF_8);
        assertTrue(AESUtils.decrypt("synthetic+key", token).contains("\"agentId\""));
    }

    @Test
    void realWebsocketRoundTripUsesOnlyTheReviewedLoopbackWithoutDefaultProxy() throws Exception {
        var proxyCalls = new AtomicInteger();
        ProxySelector previous = ProxySelector.getDefault();
        try (var server = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"));
                var executor = Executors.newSingleThreadExecutor()) {
            ProxySelector.setDefault(new ProxySelector() {
                @Override public List<Proxy> select(URI uri) {
                    if ("127.0.0.1".equals(uri.getHost()) && uri.getPort() == server.getLocalPort()) {
                        proxyCalls.incrementAndGet();
                        throw new AssertionError("MCP fixture must not use the default proxy");
                    }
                    // Other full-suite fixtures may have background connection attempts.
                    return previous == null ? List.of(Proxy.NO_PROXY) : previous.select(uri);
                }
                @Override public void connectFailed(URI uri, SocketAddress address, java.io.IOException error) {}
            });
            server.setSoTimeout(5000);
            var fixture = executor.submit(() -> {
                try (var socket = server.accept()) {
                    socket.setSoTimeout(5000);
                    InputStream input = socket.getInputStream();
                    OutputStream output = socket.getOutputStream();
                    String handshake = readHeaders(input);
                    assertTrue(handshake.startsWith("GET /call/?token="));
                    String key = handshake.lines().filter(line -> line.toLowerCase().startsWith("sec-websocket-key:"))
                            .findFirst().orElseThrow().split(":", 2)[1].trim();
                    String accept = Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1")
                            .digest((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").getBytes(StandardCharsets.US_ASCII)));
                    output.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "
                            + accept + "\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                    output.flush();
                    assertTrue(readText(input).contains("initialize"));
                    writeText(output, "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}");
                    assertTrue(readText(input).contains("notifications/initialized"));
                    assertTrue(readText(input).contains("tools/list"));
                    writeText(output, "{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"name\":\"z-tool\"},{\"name\":\"a-tool\"}]}}");
                    return true;
                }
            });
            var params = mock(SysParamsService.class);
            when(params.getValue(Constant.SERVER_MCP_ENDPOINT, true)).thenReturn(
                    "http://127.0.0.1:" + server.getLocalPort() + "/mcp?key=synthetic-key");
            assertEquals(List.of("a-tool", "z-tool"), new AgentMcpAccessPointServiceImpl(params).getAgentMcpToolsList("synthetic-agent"));
            assertTrue(fixture.get(5, TimeUnit.SECONDS));
            assertEquals(0, proxyCalls.get());
        } finally { ProxySelector.setDefault(previous); }
    }

    @ParameterizedTest
    @ValueSource(ints = {301, 302, 303, 307, 308})
    void realHandshakeRedirectNeverReachesAnotherRecipientAndLogsAreRedacted(int status) throws Exception {
        var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        var initial = new AtomicInteger();
        var redirected = new AtomicInteger();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        server.createContext("/call/", exchange -> {
            initial.incrementAndGet();
            exchange.getResponseHeaders().set("Location", base + "/trap?key=synthetic-secret");
            byte[] body = "synthetic-secret raw-response-body https://unknown.example/private".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(status, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        server.createContext("/trap", exchange -> { redirected.incrementAndGet(); exchange.close(); });
        var logs = new ListAppender<ILoggingEvent>();
        logs.start();
        var logger = (Logger) LoggerFactory.getLogger(AgentMcpAccessPointServiceImpl.class);
        logger.addAppender(logs);
        server.start();
        try {
            var params = mock(SysParamsService.class);
            when(params.getValue(Constant.SERVER_MCP_ENDPOINT, true)).thenReturn(base + "/mcp?key=synthetic-secret");
            assertEquals(List.of(), new AgentMcpAccessPointServiceImpl(params).getAgentMcpToolsList("synthetic-agent"));
            assertEquals(1, initial.get());
            assertEquals(0, redirected.get());
            assertFalse(logs.list.isEmpty());
            for (var event : logs.list) {
                assertFalse(event.getFormattedMessage().contains("synthetic-secret"));
                assertFalse(event.getFormattedMessage().contains("raw-response-body"));
                assertFalse(event.getFormattedMessage().contains("unknown.example"));
                assertFalse(event.getFormattedMessage().contains("token="));
                assertNull(event.getThrowableProxy());
            }
        } finally { server.stop(0); logger.detachAppender(logs); logs.stop(); }
    }

    private static String readHeaders(InputStream input) throws Exception {
        var bytes = new java.io.ByteArrayOutputStream();
        while (bytes.size() < 16_384) {
            int value = input.read();
            if (value < 0) throw new java.io.EOFException();
            bytes.write(value);
            String text = bytes.toString(StandardCharsets.US_ASCII);
            if (text.endsWith("\r\n\r\n")) return text;
        }
        throw new java.io.IOException("Oversized fixture handshake");
    }

    private static String readText(InputStream input) throws Exception {
        var data = new DataInputStream(input);
        assertEquals(0x81, data.readUnsignedByte());
        int second = data.readUnsignedByte();
        assertTrue((second & 0x80) != 0);
        int length = second & 0x7f;
        if (length == 126) length = data.readUnsignedShort();
        assertTrue(length < 16_384);
        byte[] mask = data.readNBytes(4);
        byte[] body = data.readNBytes(length);
        for (int i = 0; i < body.length; i++) body[i] ^= mask[i % 4];
        return new String(body, StandardCharsets.UTF_8);
    }

    private static void writeText(OutputStream output, String text) throws Exception {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        output.write(0x81);
        if (bytes.length < 126) output.write(bytes.length);
        else { output.write(126); output.write(bytes.length >>> 8); output.write(bytes.length & 255); }
        output.write(bytes);
        output.flush();
    }
}
