package xiaozhi.common.config;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import java.net.Proxy;
import java.net.URI;
import java.net.http.HttpClient;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.client.ExpectedCount;
import org.springframework.test.web.client.MockRestServiceServer;

class OptionalServiceRestTemplateConfigTest {
    @Test
    void genericBeanIsNotAnExternalServiceBypass() {
        var template = new RestTemplateConfig().restTemplate();
        var server = MockRestServiceServer.bindTo(template).build();
        server.expect(ExpectedCount.never(), requestTo("https://api.openai.com/v1"));
        assertThrows(IllegalArgumentException.class, () -> template.postForEntity(
                "https://api.openai.com/v1", "synthetic-private-body", String.class));
        assertThrows(IllegalArgumentException.class, () -> template.getForObject(
                "http://192.168.1.2/private?key=synthetic-secret", String.class));
        server.verify();
    }

    @Test
    void websocketTransportIsDirectAndNeverRedirects() throws Exception {
        try (var client = RestTemplateConfig.directHttpClient(Duration.ofSeconds(1))) {
            assertEquals(HttpClient.Redirect.NEVER, client.followRedirects());
            assertEquals(java.util.List.of(Proxy.NO_PROXY), client.proxy().orElseThrow()
                    .select(URI.create("ws://127.0.0.1:9999/mcp/?token=synthetic")));
            // No custom trust manager or SSLContext is installed by this transport.
            assertSame(javax.net.ssl.SSLContext.getDefault(), client.sslContext());
        }
    }
}
