package xiaozhi.modules.knowledge.rag;

import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.Map;

import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.text.SimpleDateFormat;
import java.util.TimeZone;
import java.util.Locale;
import java.net.URLEncoder;
import java.net.URI;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.function.Consumer;

import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.ApprovedServicePolicy;

/**
 * RAGFlow HTTP Client
 * Centralize HTTP communication, authentication, timeouts, and error parsing
 */
@Slf4j
public class RAGFlowClient {

    private final String baseUrl;
    private final String apiKey;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    // Default timeout in seconds
    private static final int DEFAULT_TIMEOUT = 30;

    public RAGFlowClient(String baseUrl, String apiKey) {
        this(baseUrl, apiKey, DEFAULT_TIMEOUT);
    }

    public RAGFlowClient(String baseUrl, String apiKey, int timeoutSeconds) {
        URI approved = approvedEndpoint(baseUrl);
        if (approved.getRawQuery() != null) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "RAGFlow base URL must not contain a query");
        }
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.apiKey = apiKey;
        this.objectMapper = new ObjectMapper();
        // [Reinforce] Accept RAGFlow RFC 1123 dates (for example, Tue, 10 Feb 2026 10:27:35 GMT)
        this.objectMapper
                .setDateFormat(new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss 'GMT'", Locale.US));
        this.objectMapper.setTimeZone(TimeZone.getTimeZone("GMT"));

        this.restTemplate = ApprovedServicePolicy.restTemplate("context");
        // Retain the constructor's per-client timeout without relaxing the transport policy.
        var factory = new org.springframework.http.client.JdkClientHttpRequestFactory(
                xiaozhi.common.config.RestTemplateConfig.directHttpClient(java.time.Duration.ofSeconds(timeoutSeconds)));
        factory.setReadTimeout(java.time.Duration.ofSeconds(timeoutSeconds));
        this.restTemplate.setRequestFactory(factory);
    }

    /**
     * Send a GET request
     */
    public Map<String, Object> get(String endpoint, Map<String, Object> queryParams) {
        String url = buildUrl(endpoint, queryParams);
        return execute(url, HttpMethod.GET, null);
    }

    /**
     * Send a POST request with JSON
     */
    public Map<String, Object> post(String endpoint, Object body) {
        String url = buildUrl(endpoint, null);
        return execute(url, HttpMethod.POST, body);
    }

    /**
     * Send a DELETE request
     */
    public Map<String, Object> delete(String endpoint, Object body) {
        String url = buildUrl(endpoint, null);
        return execute(url, HttpMethod.DELETE, body);
    }

    /**
     * Send a PUT request
     */
    public Map<String, Object> put(String endpoint, Object body) {
        String url = buildUrl(endpoint, null);
        return execute(url, HttpMethod.PUT, body);
    }

    /**
     * Send a multipart file upload request
     */
    public Map<String, Object> postMultipart(String endpoint, MultiValueMap<String, Object> parts) {
        String url = buildUrl(endpoint, null);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        headers.setBearerAuth(apiKey);
        // Some environments require a charset for Chinese file names; multipart encoding is usually controlled by the part header

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(parts, headers);

        return doExecute(url, HttpMethod.POST, requestEntity);
    }

    private Map<String, Object> execute(String url, HttpMethod method, Object body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(apiKey);
        // Force UTF-8
        headers.setAcceptCharset(Collections.singletonList(StandardCharsets.UTF_8));

        HttpEntity<Object> requestEntity = new HttpEntity<>(body, headers);
        return doExecute(url, method, requestEntity);
    }

    private Map<String, Object> doExecute(String url, HttpMethod method, HttpEntity<?> requestEntity) {
        try {
            approvedEndpoint(url);
            ResponseEntity<String> response = restTemplate.exchange(URI.create(url), method, requestEntity, String.class);

            if (!response.getStatusCode().is2xxSuccessful()) {
                log.error("RAGFlow API Error Status: {}", response.getStatusCode());
                throw new RenException(ErrorCode.RAG_API_ERROR, "HTTP " + response.getStatusCode());
            }

            String responseBody = response.getBody();
            if (responseBody == null) {
                throw new RenException(ErrorCode.RAG_API_ERROR, "Empty Response");
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> map = objectMapper.readValue(responseBody, Map.class);

            Integer code = (Integer) map.get("code");
            if (code != null && code != 0) {
                log.warn("RAGFlow returned an unsuccessful result");
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAGFlow operation failed");
            }

            // Return data, or the whole map if absent (RAGFlow usually returns code=0, data=...)
            // Compatibility: code has already been checked here for external callers
            // Return the code-wrapped map, or only data?
            // The previous logic checked code==0 before extracting data
            // Return the full map for the adapter to interpret, or unwrap here?
            // Recommendation: return the full map for flexibility, but throw on code!=0 in the client
            return map;

        } catch (RenException re) {
            throw re;
        } catch (Exception e) {
            log.warn("RAGFlow request failed");
            throw new RenException(ErrorCode.RAG_API_ERROR, "Request failed; check the reviewed RAGFlow configuration");
        }
    }

    private String buildUrl(String endpoint, Map<String, Object> queryParams) {
        if (endpoint == null || endpoint.startsWith("//")) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "Invalid RAGFlow request path");
        }
        try {
            URI path = URI.create(endpoint);
            if (path.isAbsolute() || path.getRawAuthority() != null || path.getRawQuery() != null
                    || path.getRawFragment() != null || endpoint.indexOf('\\') >= 0) {
                throw new IllegalArgumentException();
            }
        } catch (RuntimeException e) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "Invalid RAGFlow request path");
        }
        StringBuilder sb = new StringBuilder(baseUrl);
        if (!endpoint.startsWith("/")) {
            sb.append("/");
        }
        sb.append(endpoint);

        if (queryParams != null && !queryParams.isEmpty()) {
            queryParams.forEach((k, v) -> {
                if (v != null) {
                    sb.append(sb.indexOf("?") < 0 ? "?" : "&")
                            .append(URLEncoder.encode(k, StandardCharsets.UTF_8)).append("=")
                            .append(URLEncoder.encode(v.toString(), StandardCharsets.UTF_8));
                }
            });
        }
        String url = sb.toString();
        approvedEndpoint(url);
        return url;
    }

    private static URI approvedEndpoint(String url) {
        try {
            return ApprovedServicePolicy.validateEndpoint(url, "context");
        } catch (IllegalArgumentException e) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "RAGFlow is unavailable; configure a reviewed loopback endpoint");
        }
    }

    /**
     * Send a streaming POST request (SSE)
     * Uses the same guarded transport as ordinary requests.
     *
     * @param endpoint API endpoint
     * @param body request body
     * @param onData callback invoked for each data line
     */
    public void postStream(String endpoint, Object body, Consumer<String> onData) {
        try {
            String url = buildUrl(endpoint, null);
            restTemplate.execute(URI.create(url), HttpMethod.POST, request -> {
                request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
                request.getHeaders().setBearerAuth(apiKey);
                objectMapper.writeValue(request.getBody(), body);
            }, response -> {
                if (!response.getStatusCode().is2xxSuccessful()) {
                    throw new RenException(ErrorCode.RAG_API_ERROR, "RAGFlow stream request failed");
                }
                try (var reader = new BufferedReader(new InputStreamReader(response.getBody(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (!line.isBlank()) onData.accept(line);
                    }
                }
                return null;
            });
        } catch (RenException e) {
            throw e;
        } catch (Exception e) {
            log.warn("RAGFlow stream request failed");
            throw new RenException(ErrorCode.RAG_API_ERROR, "Stream request failed; check the reviewed RAGFlow configuration");
        }
    }
}
