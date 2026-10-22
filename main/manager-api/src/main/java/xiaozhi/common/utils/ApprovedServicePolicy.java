package xiaozhi.common.utils;

import java.io.IOException;
import java.net.IDN;
import java.net.Proxy;
import java.net.ProxySelector;
import java.net.SocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/** Small operator-owned origin policy, paired with config/service_policy.py. */
public final class ApprovedServicePolicy {
    private ApprovedServicePolicy() {}

    private static final Set<String> ROLES = Set.of("asr", "llm", "vllm", "tts", "context", "tool", "mcp", "memory", "voiceprint");
    private static final Map<String, Set<String>> CLOUD = Map.of(
            "api.openai.com", Set.of("asr", "llm", "vllm", "tts"),
            "generativelanguage.googleapis.com", Set.of("llm", "vllm"));
    private static final Set<String> SECRET_QUERY = Set.of("api_key", "apikey", "key", "token", "access_token", "secret", "signature");

    private static IllegalArgumentException rejected() {
        // Never include a supplied URL, authority, token or response body.
        return new IllegalArgumentException("Service destination is not approved for this capability; select a reviewed endpoint");
    }

    public static URI validateEndpoint(String url, String role) {
        if (role == null || !ROLES.contains(role) || url == null || url.isEmpty() || url.indexOf('\\') >= 0
                || url.chars().anyMatch(c -> c <= 32)) throw rejected();
        try {
            URI uri = URI.create(url);
            if (uri.getRawUserInfo() != null || uri.getRawFragment() != null || uri.getHost() == null) throw rejected();
            String host = uri.getHost().toLowerCase(Locale.ROOT);
            if (host.endsWith(".")) host = host.substring(0, host.length() - 1);
            if (host.startsWith("[") && host.endsWith("]")) host = host.substring(1, host.length() - 1);
            if (host.contains("%")) throw rejected();
            if (!host.contains(":")) host = IDN.toASCII(host).toLowerCase(Locale.ROOT);
            int port = uri.getPort();
            if (port == 0 || port > 65535 || port < -1) throw rejected();
            if (Set.of("asr", "llm", "vllm", "tts").contains(role) && uri.getRawQuery() != null) {
                for (String pair : uri.getRawQuery().split("&")) {
                    String key = URLDecoder.decode(pair.split("=", 2)[0], StandardCharsets.UTF_8).toLowerCase(Locale.ROOT);
                    if (SECRET_QUERY.contains(key)) throw rejected();
                }
            }
            boolean loopback = host.equals("localhost") || host.equals("::1") || host.equals("0:0:0:0:0:0:0:1");
            if (host.matches("127\\.[0-9]+\\.[0-9]+\\.[0-9]+")) {
                loopback = java.util.Arrays.stream(host.split("\\.")).allMatch(part ->
                        part.equals("0") || (!part.startsWith("0") && part.length() <= 3 && Integer.parseInt(part) <= 255));
            }
            String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
            if (loopback && (Set.of("http", "https").contains(scheme)
                    || (role.equals("mcp") && Set.of("ws", "wss").contains(scheme)))) return uri;
            if (scheme.equals("https") && (port == -1 || port == 443)
                    && CLOUD.getOrDefault(host, Set.of()).contains(role)) return uri;
        } catch (RuntimeException ignored) {
            // Parse failures are redacted in exactly the same way as policy failures.
        }
        throw rejected();
    }

    public static RestTemplate restTemplate(String role) {
        if (role == null || !ROLES.contains(role)) throw rejected();
        var direct = new ProxySelector() {
            @Override public List<Proxy> select(URI uri) { return List.of(Proxy.NO_PROXY); }
            @Override public void connectFailed(URI uri, SocketAddress address, IOException error) {}
        };
        var client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NEVER).proxy(direct).build();
        var factory = new JdkClientHttpRequestFactory(client);
        factory.setReadTimeout(Duration.ofSeconds(30));
        var template = new RestTemplate(factory);
        template.getInterceptors().add((request, body, execution) -> {
            validateEndpoint(request.getURI().toString(), role);
            var response = execution.execute(request, body);
            if (response.getStatusCode().is3xxRedirection()) {
                response.close();
                throw new IllegalArgumentException("Service redirected; configure a reviewed final endpoint explicitly");
            }
            return response;
        });
        return template;
    }
}
