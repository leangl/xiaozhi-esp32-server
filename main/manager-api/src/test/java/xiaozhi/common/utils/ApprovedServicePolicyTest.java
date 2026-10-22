package xiaozhi.common.utils;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.client.ExpectedCount;
import org.springframework.test.web.client.MockRestServiceServer;

class ApprovedServicePolicyTest {
    @ParameterizedTest
    @ValueSource(strings = {"https://api.openai.com/v1", "https://API.OPENAI.COM.:443/v1",
            "https://generativelanguage.googleapis.com/v1beta/openai", "http://localhost:8880/v1",
            "http://127.0.0.1:8080/v1", "https://[::1]:8080/v1"})
    void reviewedChatOriginsAreAccepted(String url) {
        assertNotNull(ApprovedServicePolicy.validateEndpoint(url, "llm"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "https://api.deepseek.com/v1", "https://open.bigmodel.cn/v1",
            "https://api.openai.com.evil.example/v1", "https://api.openai.com@evil.example/v1",
            "https://user:private-secret@api.openai.com/v1", "https://unknown.example/v1",
            "http://api.openai.com/v1", "https://api.openai.com:444/v1", "https://api.openai.com/#private-secret",
            "https://api.openai.com\\@evil.example/v1", "https://api.openai.com\n.evil.example/v1",
            "file:///private/data", "ftp://localhost/data", "http://127.1:8080/v1",
            "http://169.254.169.254/latest/meta-data", "https://api.openai.com:0/v1",
            "https://api.openai.com:99999/v1", "https://[broken", "https://api%2eopenai.com/v1",
            "https://api.openai.com/v1?api_key=private-secret"})
    void removedUnknownAndMalformedOriginsAreRedacted(String url) {
        var error = assertThrows(IllegalArgumentException.class,
                () -> ApprovedServicePolicy.validateEndpoint(url, "llm"));
        assertFalse(error.getMessage().contains("private-secret"));
        if (!url.isEmpty()) assertFalse(error.getMessage().contains(url));
    }

    @Test
    void capabilitiesAreNotInterchangeableAndNullIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> ApprovedServicePolicy.validateEndpoint(null, "llm"));
        assertThrows(IllegalArgumentException.class, () -> ApprovedServicePolicy.validateEndpoint("https://api.openai.com", null));
        assertThrows(IllegalArgumentException.class, () -> ApprovedServicePolicy.validateEndpoint("https://api.openai.com", "context"));
        assertThrows(IllegalArgumentException.class, () -> ApprovedServicePolicy.validateEndpoint("https://generativelanguage.googleapis.com", "tts"));
    }

    @Test
    void rejectedRequestsNeverReachTheRequestFactory() {
        var template = ApprovedServicePolicy.restTemplate("llm");
        var server = MockRestServiceServer.bindTo(template).build();
        server.expect(ExpectedCount.never(), requestTo("https://api.deepseek.com/v1"));
        assertThrows(IllegalArgumentException.class, () -> template.postForEntity(
                "https://api.deepseek.com/v1", "synthetic-body", String.class));
        server.verify();
    }

    @Test
    void redirectsDoNotSendAnotherRequest() {
        var template = ApprovedServicePolicy.restTemplate("llm");
        var server = MockRestServiceServer.bindTo(template).build();
        server.expect(requestTo("https://api.openai.com/v1"))
                .andRespond(withStatus(HttpStatus.TEMPORARY_REDIRECT).location(java.net.URI.create("https://unknown.example/receive")));
        assertThrows(IllegalArgumentException.class, () -> template.postForEntity(
                "https://api.openai.com/v1", "synthetic-body", String.class));
        server.verify();
    }
}
