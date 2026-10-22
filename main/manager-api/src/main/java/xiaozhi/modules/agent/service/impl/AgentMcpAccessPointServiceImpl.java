package xiaozhi.modules.agent.service.impl;

import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLEncoder;
import java.net.URLDecoder;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.function.Predicate;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import cn.hutool.crypto.digest.DigestUtil;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.utils.AESUtils;
import xiaozhi.common.utils.ApprovedServicePolicy;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.Enums.XiaoZhiMcpJsonRpcJson;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;
import xiaozhi.modules.sys.service.SysParamsService;

@AllArgsConstructor
@Service
@Slf4j
public class AgentMcpAccessPointServiceImpl implements AgentMcpAccessPointService {
    private SysParamsService sysParamsService;

    @Override
    public String getAgentMcpAccessAddress(String id) {
        // Get the MCP URL
        String url = sysParamsService.getValue(Constant.SERVER_MCP_ENDPOINT, true);
        if (StringUtils.isBlank(url) || "null".equals(url)) {
            return null;
        }
        try {
            URI uri = getURI(url);
            String agentMcpUrl = getAgentMcpUrl(uri);
            String key = getSecretKey(uri);
            String encryptToken = encryptToken(id, key);
            String encodedToken = URLEncoder.encode(encryptToken, StandardCharsets.UTF_8);
            agentMcpUrl = "%s/mcp/?token=%s".formatted(agentMcpUrl, encodedToken);
            ApprovedServicePolicy.validateEndpoint(agentMcpUrl, "mcp");
            return agentMcpUrl;
        } catch (RuntimeException e) {
            log.warn("MCP access point unavailable; configure a reviewed loopback endpoint");
            return null;
        }
    }

    @Override
    public List<String> getAgentMcpToolsList(String id) {
        String wsUrl = getAgentMcpAccessAddress(id);
        if (StringUtils.isBlank(wsUrl)) {
            return List.of();
        }

        // Replace /mcp with /call
        wsUrl = wsUrl.replace("/mcp/", "/call/");

        try {
            ApprovedServicePolicy.validateEndpoint(wsUrl, "mcp");
            // Direct connection, eight-second handshake and a bounded total session.
            try (McpSocket client = new McpSocket(URI.create(wsUrl))) {

                // Step 1: send initialization and wait for a response
                log.info("Sending MCP initialization, agent ID: {}", id);
                client.sendText(XiaoZhiMcpJsonRpcJson.getInitializeJson());

                // Wait for initialization response (id=1), driven by responses instead of a fixed delay
                List<String> initResponses = client.listenerWithoutClose(response -> {
                    try {
                        Map<String, Object> jsonMap = JsonUtils.parseMap(response);
                        if (jsonMap != null && Integer.valueOf(1).equals(jsonMap.get("id"))) {
                            // Check for a result field indicating successful initialization
                            return jsonMap.containsKey("result") && !jsonMap.containsKey("error");
                        }
                        return false;
                    } catch (Exception e) {
                        log.warn("Invalid MCP initialization response");
                        return false;
                    }
                });

                // Validate the initialization response
                boolean initSucceeded = false;
                for (String response : initResponses) {
                    try {
                        Map<String, Object> jsonMap = JsonUtils.parseMap(response);
                        if (jsonMap != null && Integer.valueOf(1).equals(jsonMap.get("id"))) {
                            if (jsonMap.containsKey("result")) {
                                log.info("MCP initialized, agent ID: {}", id);
                                initSucceeded = true;
                                break;
                            } else if (jsonMap.containsKey("error")) {
                                log.error("MCP initialization failed");
                                return List.of();
                            }
                        }
                    } catch (Exception e) {
                        log.warn("Invalid MCP initialization response");
                    }
                }

                if (!initSucceeded) {
                    log.error("No valid MCP initialization response, agent ID: {}", id);
                    return List.of();
                }

                // Step 2: send the initialized notification only after receiving the initialize response
                log.info("Sending MCP initialized notification, agent ID: {}", id);
                client.sendText(XiaoZhiMcpJsonRpcJson.getNotificationsInitializedJson());
                // Step 3: send the tool list request immediately, without an extra delay
                log.info("Sending MCP tool list request, agent ID: {}", id);
                client.sendText(XiaoZhiMcpJsonRpcJson.getToolsListJson());

                // Wait for the tool list response (id=2)
                List<String> toolsResponses = client.listener(response -> {
                    try {
                        Map<String, Object> jsonMap = JsonUtils.parseMap(response);
                        return jsonMap != null && Integer.valueOf(2).equals(jsonMap.get("id"));
                    } catch (Exception e) {
                        log.warn("Invalid MCP tool list response");
                        return false;
                    }
                });

                // Process the tool list response
                for (String response : toolsResponses) {
                    try {
                        Map<String, Object> jsonMap = JsonUtils.parseMap(response);
                        if (jsonMap != null && Integer.valueOf(2).equals(jsonMap.get("id"))) {
                            // Check for a result field
                            Object resultObj = jsonMap.get("result");
                            if (resultObj instanceof Map<?, ?>) {
                                Map<String, Object> resultMap = JsonUtils.toStringObjectMap(resultObj);
                                Object toolsObj = resultMap.get("tools");
                                if (toolsObj instanceof List<?>) {
                                    List<Map<String, Object>> toolsList = JsonUtils.toStringObjectMapList(toolsObj);
                                    // Extract the tool names
                                    List<String> result = toolsList.stream()
                                            .map(tool -> String.class.cast(tool.get("name")))
                                            .filter(name -> name != null)
                                            .sorted()
                                            .collect(Collectors.toList());
                                    log.info("Retrieved MCP tool list, agent ID: {}, tool count: {}", id, result.size());
                                    return result;
                                }
                            } else if (jsonMap.containsKey("error")) {
                                log.error("Failed to get MCP tool list");
                                return List.of();
                            }
                        }
                    } catch (Exception e) {
                        log.warn("Invalid MCP tool list response");
                    }
                }

                log.warn("No valid tool list response, agent ID: {}", id);
                return List.of();

            }
        } catch (Exception e) {
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            log.error("MCP tools unavailable");
            return List.of();
        }
    }

    /**
     * Get the URI object
     * 
     * @param url URL
     * @return URI object
     */
    private static URI getURI(String url) {
        return ApprovedServicePolicy.validateEndpoint(url, "mcp");
    }

    /**
     * Get the secret
     *
     * @param uri MCP URL
     * @return secret
     */
    private static String getSecretKey(URI uri) {
        // Get parameters
        String query = uri.getRawQuery();
        if (query == null) throw new IllegalArgumentException("MCP key is not configured");
        List<String> keys = Arrays.stream(query.split("&")).filter(pair -> pair.startsWith("key="))
                .map(pair -> pair.substring(4)).toList();
        if (keys.size() != 1 || keys.getFirst().isBlank()) {
            throw new IllegalArgumentException("MCP key is not configured");
        }
        return URLDecoder.decode(keys.getFirst().replace("+", "%2B"), StandardCharsets.UTF_8);
    }

    /**
     * Get the agent MCP access point URL
     *
     * @param uri MCP URL
     * @return agent MCP access point URL
     */
    private String getAgentMcpUrl(URI uri) {
        // Get the protocol
        String wsScheme = (uri.getScheme().equalsIgnoreCase("https") || uri.getScheme().equalsIgnoreCase("wss")) ? "wss" : "ws";
        // Get host, port, and path
        String path = uri.getPath();
        // Get the path before the last slash
        path = path.substring(0, Math.max(0, path.lastIndexOf("/")));
        try {
            return new URI(wsScheme, uri.getRawAuthority(), path, null, null).toString();
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("Invalid MCP access point");
        }
    }

    /**
     * Get the token encrypting the agent ID
     *
     * @param agentId agent ID
     * @param key encryption key
     * @return encrypted token
     */
    private static String encryptToken(String agentId, String key) {
        // Hash the agent ID using MD5
        String md5 = DigestUtil.md5Hex(agentId);
        // Text to encrypt with AES
        String json = "{\"agentId\": \"%s\"}".formatted(md5);
        // Encrypt to obtain the token value
        return AESUtils.encrypt(key, json);
    }

    /** Bounded direct transport; never delegates token-bearing URLs to the shared WS logger. */
    private static final class McpSocket implements AutoCloseable, WebSocket.Listener {
        private final HttpClient httpClient = RestTemplateConfig.directHttpClient(Duration.ofSeconds(8));
        private final ArrayBlockingQueue<String> messages = new ArrayBlockingQueue<>(100);
        private final CompletableFuture<Void> failed = new CompletableFuture<>();
        private final StringBuilder partial = new StringBuilder();
        private final long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(18);
        private WebSocket socket;

        private McpSocket(URI uri) throws Exception {
            try {
                ApprovedServicePolicy.validateEndpoint(uri.toString(), "mcp");
                socket = httpClient.newWebSocketBuilder().connectTimeout(Duration.ofSeconds(8))
                        .buildAsync(uri, this).get(8, TimeUnit.SECONDS);
            } catch (Exception e) {
                httpClient.shutdownNow();
                throw e;
            }
        }

        @Override public void onOpen(WebSocket webSocket) { webSocket.request(1); }

        @Override public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
            if (partial.length() + data.length() > 1024 * 1024) {
                failed.completeExceptionally(new IllegalStateException("MCP response exceeds limit"));
                webSocket.abort();
                return null;
            }
            partial.append(data);
            if (last) {
                if (!messages.offer(partial.toString())) {
                    failed.completeExceptionally(new IllegalStateException("MCP response queue exceeds limit"));
                    webSocket.abort();
                }
                partial.setLength(0);
            }
            webSocket.request(1);
            return null;
        }

        @Override public void onError(WebSocket webSocket, Throwable error) {
            failed.completeExceptionally(new IllegalStateException("MCP transport failed"));
        }

        @Override public CompletionStage<?> onClose(WebSocket webSocket, int status, String reason) {
            failed.completeExceptionally(new IllegalStateException("MCP connection closed"));
            return null;
        }

        private void sendText(String text) throws Exception {
            socket.sendText(text, true).get(remainingMillis(), TimeUnit.MILLISECONDS);
        }

        private long remainingMillis() throws java.util.concurrent.TimeoutException {
            long remaining = TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime());
            if (remaining <= 0) throw new java.util.concurrent.TimeoutException("MCP request timed out");
            return remaining;
        }

        private List<String> listenerWithoutClose(Predicate<String> predicate) throws Exception {
            List<String> result = new ArrayList<>();
            do {
                String message = messages.poll(Math.min(remainingMillis(), 100), TimeUnit.MILLISECONDS);
                if (message != null) {
                    if (result.size() >= 100) throw new IllegalStateException("MCP response count exceeds limit");
                    result.add(message);
                    if (predicate.test(message)) return result;
                } else if (failed.isDone()) {
                    failed.get();
                }
            } while (true);
        }

        private List<String> listener(Predicate<String> predicate) throws Exception {
            return listenerWithoutClose(predicate);
        }

        @Override public void close() {
            if (socket != null) socket.abort();
            httpClient.shutdownNow();
        }
    }
}
