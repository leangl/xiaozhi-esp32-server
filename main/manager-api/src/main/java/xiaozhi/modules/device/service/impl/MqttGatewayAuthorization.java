package xiaozhi.modules.device.service.impl;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.Duration;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Function;

import org.apache.commons.lang3.StringUtils;

import cn.hutool.crypto.digest.DigestUtil;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.utils.ApprovedServicePolicy;

final class MqttGatewayAuthorization {

    private static final int HTTP_UNAUTHORIZED = 401;
    private static final int DEFAULT_TIMEOUT_MILLIS = 10000;
    private static final int MAX_TIMEOUT_MILLIS = 30000;

    private MqttGatewayAuthorization() {
    }

    static String postJson(String url, String jsonBody, String signatureKey, Instant now) {
        return postJson(url, jsonBody, signatureKey, now, DEFAULT_TIMEOUT_MILLIS);
    }

    static String postJson(String url, String jsonBody, String signatureKey, Instant now, int timeoutMillis) {
        URI target = approvedTarget(url);
        if (timeoutMillis <= 0 || timeoutMillis > MAX_TIMEOUT_MILLIS) {
            throw new GatewayRequestException("MQTT Gateway timeout must be between 1 and 30000 milliseconds", null);
        }
        HttpClient client = RestTemplateConfig.directHttpClient(Duration.ofMillis(timeoutMillis));
        GatewayResponse response;
        try {
            response = executeWithDateFallback(signatureKey, now,
                    token -> executeRequest(client, target, jsonBody, token, timeoutMillis));
        } finally {
            client.shutdownNow();
        }

        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new GatewayRequestException(
                    "MQTT Gateway request failed with HTTP status " + response.statusCode(),
                    response.statusCode());
        }
        return response.body();
    }

    static List<String> generateDailyTokens(String signatureKey, Instant now) {
        if (isMissingSignatureKey(signatureKey)) {
            throw new GatewayRequestException("MQTT Gateway signature key is empty", null);
        }

        LocalDate utcDate = now.atZone(ZoneOffset.UTC).toLocalDate();
        return List.of(
                tokenFor(utcDate, signatureKey),
                tokenFor(utcDate.minusDays(1), signatureKey),
                tokenFor(utcDate.plusDays(1), signatureKey));
    }

    static GatewayResponse executeWithDateFallback(String signatureKey, Instant now,
            Function<String, GatewayResponse> requestExecutor) {
        GatewayResponse lastAuthenticationFailure = null;
        for (String token : generateDailyTokens(signatureKey, now)) {
            GatewayResponse response = requestExecutor.apply(token);
            if (!isAuthenticationFailure(response.statusCode())) {
                return response;
            }
            lastAuthenticationFailure = response;
        }

        Integer statusCode = lastAuthenticationFailure == null ? null : lastAuthenticationFailure.statusCode();
        throw new GatewayRequestException(
                "MQTT Gateway rejected all daily authorization tokens"
                        + (statusCode == null ? "" : " (HTTP " + statusCode + ")"),
                statusCode);
    }

    private static String tokenFor(LocalDate date, String signatureKey) {
        return DigestUtil.sha256Hex(date + signatureKey);
    }

    private static boolean isAuthenticationFailure(int statusCode) {
        return statusCode == HTTP_UNAUTHORIZED;
    }

    static boolean isMissingSignatureKey(String signatureKey) {
        return StringUtils.isBlank(signatureKey) || "null".equalsIgnoreCase(signatureKey.trim());
    }

    private static URI approvedTarget(String url) {
        try {
            return ApprovedServicePolicy.validateEndpoint(url, "tool");
        } catch (IllegalArgumentException e) {
            throw new GatewayRequestException("MQTT Gateway is unavailable; configure a reviewed loopback endpoint", null);
        }
    }

    private static GatewayResponse executeRequest(HttpClient client, URI target, String jsonBody, String token, int timeoutMillis) {
        // Validate the final recipient again on every attempt before attaching authorization.
        approvedTarget(target.toString());
        try {
            HttpRequest request = HttpRequest.newBuilder(target)
                    .timeout(Duration.ofMillis(timeoutMillis))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + token)
                    .POST(HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8)).build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            return new GatewayResponse(response.statusCode(), response.body());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new GatewayRequestException("MQTT Gateway request interrupted", null);
        } catch (java.io.IOException | RuntimeException e) {
            // Do not propagate request URIs, authorization headers, response bodies or causes.
            throw new GatewayRequestException("MQTT Gateway request failed", null);
        }
    }

    record GatewayResponse(int statusCode, String body) {
    }

    static final class GatewayRequestException extends RuntimeException {
        private final Integer statusCode;

        GatewayRequestException(String message, Integer statusCode) {
            super(message);
            this.statusCode = statusCode;
        }

        Integer statusCode() {
            return statusCode;
        }
    }
}
