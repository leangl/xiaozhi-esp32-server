package xiaozhi.modules.llm.service.impl;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.llm.service.LLMService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.common.utils.ApprovedProviderCatalog;

/**
 * LLM service implementation for OpenAI-style APIs
 * Uses supported models only after catalog and effective-endpoint validation.
 */
@Slf4j
@Service
public class OpenAIStyleLLMServiceImpl implements LLMService {

    @Autowired
    private ModelConfigService modelConfigService;

    private final RestTemplate restTemplate = xiaozhi.common.utils.ApprovedServicePolicy.restTemplate("llm");

    private static final String DEFAULT_SUMMARY_PROMPT = "You are an experienced memory summarizer. Summarize conversations according to these rules:\n1. Summarize important information about the user to personalize future conversations.\n2. Do not repeat summaries or forget existing memory. Do not discard or compress historical memory unless it exceeds 1800 characters.\n3. Exclude device volume changes, music playback, weather queries, exit requests, refusal to converse, and other information unrelated to the user.\n4. Exclude incidental current dates, times, and weather unrelated to user events; storing them as memory can affect later conversations.\n5. Exclude device-control successes and failures, and meaningless chatter.\n6. Do not summarize merely for its own sake. If the conversation contains nothing meaningful, returning the existing memory unchanged is acceptable.\n7. Return only the summary, in Chinese, strictly within 1800 characters.\n8. Do not include code, XML, explanations, comments, or annotations. Extract memory only from the conversation, never from examples.\n9. If historical memory is supplied, intelligently merge the new conversation into it, preserving valuable history and adding important new information.\n\nHistorical memory:\n{history_memory}\n\nNew conversation:\n{conversation}";

    private static final String DEFAULT_TITLE_PROMPT = "Generate a concise Chinese session title from the following conversation, approximately 15 characters or fewer. Return only the title, without explanations or punctuation:\n{conversation}";

    @Override
    public String generateSummary(String conversation) {
        return generateSummary(conversation, null, null);
    }

    @Override
    public String generateSummaryWithModel(String conversation, String modelId) {
        return generateSummary(conversation, null, modelId);
    }

    @Override
    public String generateSummary(String conversation, String promptTemplate, String modelId) {
        if (!isAvailable(modelId)) {
            log.warn("LLM service unavailable; cannot generate a summary");
            return "LLM service unavailable; cannot generate a summary";
        }

        try {
            // Get LLM model configuration from the management console
            ModelConfigEntity llmConfig;
            if (modelId != null && !modelId.trim().isEmpty()) {
                // Get configuration by a specific model ID
                llmConfig = modelConfigService.getModelByIdFromCache(modelId);
            } else {
                // Use the default configuration for backward compatibility
                llmConfig = getDefaultLLMConfig();
            }

            if (llmConfig == null || llmConfig.getConfigJson() == null) {
                log.error("No available LLM configuration, modelId: {}", modelId);
                return "No available LLM model configuration found";
            }

            ApprovedProviderCatalog.validateSelection("llm", llmConfig);
            JSONObject configJson = llmConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String model = configJson.getStr("model_name");
            String apiKey = configJson.getStr("api_key");
            Double temperature = configJson.getDouble("temperature");
            Integer maxTokens = configJson.getInt("max_tokens");

            if (StringUtils.isBlank(baseUrl) || StringUtils.isBlank(apiKey)) {
                log.error("LLM configuration incomplete: baseUrl or apiKey is empty");
                return "LLM configuration is incomplete; cannot generate a summary";
            }

            // Build the prompt
            String prompt = (promptTemplate != null ? promptTemplate : DEFAULT_SUMMARY_PROMPT).replace("{conversation}",
                    conversation);

            // Build the request body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model != null ? model : "gpt-3.5-turbo");

            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);

            requestBody.put("messages", List.of(message));
            requestBody.put("temperature", temperature != null ? temperature : 0.7);
            requestBody.put("max_tokens", maxTokens != null ? maxTokens : 2000);

            // Send the HTTP request
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            // Build the complete API URL
            String apiUrl = baseUrl;
            if (!apiUrl.endsWith("/chat/completions")) {
                if (!apiUrl.endsWith("/")) {
                    apiUrl += "/";
                }
                apiUrl += "chat/completions";
            }

            ResponseEntity<String> response = restTemplate.exchange(
                    apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JSONObject responseJson = JSONUtil.parseObj(response.getBody());
                JSONArray choices = responseJson.getJSONArray("choices");
                if (choices != null && choices.size() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject messageObj = choice.getJSONObject("message");
                    return messageObj.getStr("content");
                }
            } else {
                log.error("LLM API call failed, status: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("LLM summary generation failed; provider response and request details withheld");
        }

        return "Summary generation failed; retry later";
    }

    @Override
    public String generateSummary(String conversation, String promptTemplate) {
        return generateSummary(conversation, promptTemplate, null);
    }

    @Override
    public String generateSummaryWithHistory(String conversation, String historyMemory, String promptTemplate,
            String modelId) {
        if (!isAvailable(modelId)) {
            log.warn("LLM service unavailable; cannot generate a summary");
            return "LLM service unavailable; cannot generate a summary";
        }

        try {
            // Get LLM model configuration from the management console
            ModelConfigEntity llmConfig;
            if (modelId != null && !modelId.trim().isEmpty()) {
                llmConfig = modelConfigService.getModelByIdFromCache(modelId);
            } else {
                llmConfig = getDefaultLLMConfig();
            }

            if (llmConfig == null || llmConfig.getConfigJson() == null) {
                log.error("No available LLM configuration, modelId: {}", modelId);
                return "No available LLM model configuration found";
            }

            ApprovedProviderCatalog.validateSelection("llm", llmConfig);
            JSONObject configJson = llmConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String model = configJson.getStr("model_name");
            String apiKey = configJson.getStr("api_key");

            if (StringUtils.isBlank(baseUrl) || StringUtils.isBlank(apiKey)) {
                log.error("LLM configuration incomplete: baseUrl or apiKey is empty");
                return "LLM configuration is incomplete; cannot generate a summary";
            }

            // Build a prompt including existing memory
            String prompt = (promptTemplate != null ? promptTemplate : DEFAULT_SUMMARY_PROMPT)
                    .replace("{history_memory}", historyMemory != null ? historyMemory : "No historical memory")
                    .replace("{conversation}", conversation);

            // Build the request body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model != null ? model : "gpt-3.5-turbo");

            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);

            requestBody.put("messages", List.of(message));
            requestBody.put("temperature", 0.2);
            requestBody.put("max_tokens", 2000);

            // Send the HTTP request
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            // Build the complete API URL
            String apiUrl = baseUrl;
            if (!apiUrl.endsWith("/chat/completions")) {
                if (!apiUrl.endsWith("/")) {
                    apiUrl += "/";
                }
                apiUrl += "chat/completions";
            }

            ResponseEntity<String> response = restTemplate.exchange(
                    apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JSONObject responseJson = JSONUtil.parseObj(response.getBody());
                JSONArray choices = responseJson.getJSONArray("choices");
                if (choices != null && choices.size() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject messageObj = choice.getJSONObject("message");
                    return messageObj.getStr("content");
                }
            } else {
                log.error("LLM API call failed, status: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("LLM summary generation failed; provider response and request details withheld");
        }

        return "Summary generation failed; retry later";
    }

    @Override
    public boolean isAvailable() {
        try {
            ModelConfigEntity defaultLLMConfig = getDefaultLLMConfig();
            if (defaultLLMConfig == null || defaultLLMConfig.getConfigJson() == null) {
                return false;
            }

            ApprovedProviderCatalog.validateSelection("llm", defaultLLMConfig);
            JSONObject configJson = defaultLLMConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String apiKey = configJson.getStr("api_key");

            return baseUrl != null && !baseUrl.trim().isEmpty() &&
                    apiKey != null && !apiKey.trim().isEmpty();
        } catch (Exception e) {
            log.warn("LLM configuration unavailable; select a supported provider with a reviewed endpoint");
            return false;
        }
    }

    @Override
    public boolean isAvailable(String modelId) {
        try {
            if (modelId == null || modelId.trim().isEmpty()) {
                return isAvailable();
            }

            // Get configuration by a specific model ID
            ModelConfigEntity modelConfig = modelConfigService.getModelByIdFromCache(modelId);
            if (modelConfig == null || modelConfig.getConfigJson() == null) {
                log.warn("Specified LLM configuration not found, modelId: {}", modelId);
                return false;
            }

            ApprovedProviderCatalog.validateSelection("llm", modelConfig);
            JSONObject configJson = modelConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String apiKey = configJson.getStr("api_key");

            return baseUrl != null && !baseUrl.trim().isEmpty() &&
                    apiKey != null && !apiKey.trim().isEmpty();
        } catch (Exception e) {
            log.warn("LLM configuration unavailable; select a supported provider with a reviewed endpoint");
            return false;
        }
    }

    /**
     * Get the default LLM configuration from the management console
     */
    private ModelConfigEntity getDefaultLLMConfig() {
        try {
            // Get all enabled LLM configurations
            List<ModelConfigEntity> llmConfigs = modelConfigService.getEnabledModelsByType("LLM");
            if (llmConfigs == null || llmConfigs.isEmpty()) {
                return null;
            }

            // Prefer the default; otherwise use the first enabled configuration
            for (ModelConfigEntity config : llmConfigs) {
                if (config.getIsDefault() != null && config.getIsDefault() == 1) {
                    return config;
                }
            }

            return null; // No implicit replacement for an unavailable default.
        } catch (Exception e) {
            log.error("Failed to get LLM model configuration: ", e);
            return null;
        }
    }

    @Override
    public String generateTitle(String conversation, String modelId) {
        if (!isAvailable(modelId)) {
            log.warn("LLM service unavailable; cannot generate a title");
            return null;
        }

        try {
            ModelConfigEntity llmConfig;
            if (modelId != null && !modelId.trim().isEmpty()) {
                llmConfig = modelConfigService.getModelByIdFromCache(modelId);
            } else {
                llmConfig = getDefaultLLMConfig();
            }

            if (llmConfig == null || llmConfig.getConfigJson() == null) {
                log.error("No available LLM configuration, modelId: {}", modelId);
                return null;
            }

            ApprovedProviderCatalog.validateSelection("llm", llmConfig);
            JSONObject configJson = llmConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String model = configJson.getStr("model_name");
            String apiKey = configJson.getStr("api_key");

            if (StringUtils.isBlank(baseUrl) || StringUtils.isBlank(apiKey)) {
                log.error("LLM configuration incomplete: baseUrl or apiKey is empty");
                return null;
            }

            String prompt = DEFAULT_TITLE_PROMPT.replace("{conversation}", conversation);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model != null ? model : "gpt-3.5-turbo");

            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);

            requestBody.put("messages", List.of(message));
            requestBody.put("temperature", 0.3);
            requestBody.put("max_tokens", 50);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            String apiUrl = baseUrl;
            if (!apiUrl.endsWith("/chat/completions")) {
                if (!apiUrl.endsWith("/")) {
                    apiUrl += "/";
                }
                apiUrl += "chat/completions";
            }

            ResponseEntity<String> response = restTemplate.exchange(
                    apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JSONObject responseJson = JSONUtil.parseObj(response.getBody());
                JSONArray choices = responseJson.getJSONArray("choices");
                if (choices != null && choices.size() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject messageObj = choice.getJSONObject("message");
                    String title = messageObj.getStr("content");
                    if (StringUtils.isNotBlank(title)) {
                        title = title.trim().replaceAll("[，。！？、：；''\"\"【】（）]", "");
                        if (title.length() > 15) {
                            title = title.substring(0, 15);
                        }
                        return title;
                    }
                }
            } else {
                log.error("LLM API call failed, status: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("LLM title generation failed; provider response and request details withheld");
        }

        return null;
    }
}
