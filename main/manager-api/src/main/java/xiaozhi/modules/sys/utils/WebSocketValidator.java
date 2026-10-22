package xiaozhi.modules.sys.utils;

import java.net.URI;
import java.net.http.WebSocket;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.utils.ApprovedServicePolicy;

public class WebSocketValidator {
    private static final Logger logger = LoggerFactory.getLogger(WebSocketValidator.class);

    // WebSocket URL regular expression
    private static final Pattern WS_URL_PATTERN = Pattern
            .compile("^wss?://[\\w.-]+(?:\\.[\\w.-]+)*(?::\\d+)?(?:/[\\w.-]*)*$");

    /**
     * Validate the WebSocket URL format
     * 
     * @param url WebSocket URL
     * @return whether valid
     */
    public static boolean validateUrlFormat(String url) {
        if (StringUtils.isBlank(url)) {
            return false;
        }
        return WS_URL_PATTERN.matcher(url.trim()).matches();
    }

    /**
     * Test the WebSocket connection
     * 
     * @param url WebSocket URL
     * @return whether connectable
     */
    public static boolean testConnection(String url) {
        if (!validateUrlFormat(url)) {
            return false;
        }

        try {
            URI target = ApprovedServicePolicy.validateEndpoint(url, "mcp");
            var client = RestTemplateConfig.directHttpClient(Duration.ofSeconds(5));
            try {
                WebSocket socket = client.newWebSocketBuilder().connectTimeout(Duration.ofSeconds(5))
                        .buildAsync(target, new WebSocket.Listener() {}).get(5, TimeUnit.SECONDS);
                socket.abort();
                return true;
            } finally {
                client.shutdownNow();
            }
        } catch (Exception e) {
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            logger.error("WebSocket connection test failed");
            return false;
        }
    }
}
