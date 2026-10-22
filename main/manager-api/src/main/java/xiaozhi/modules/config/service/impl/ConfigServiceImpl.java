package xiaozhi.modules.config.service.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;

import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.entity.AgentContextProviderEntity;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentPluginMapping;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.entity.AgentVoicePrintEntity;
import xiaozhi.modules.agent.service.AgentContextProviderService;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.correctword.service.CorrectWordFileService;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;
import xiaozhi.modules.correctword.vo.CorrectWordSimpleVO;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.timbre.service.TimbreService;
import xiaozhi.modules.timbre.vo.TimbreDetailsVO;
import xiaozhi.modules.voiceclone.service.VoiceCloneService;

@Service
@AllArgsConstructor
public class ConfigServiceImpl implements ConfigService {
    private final SysParamsService sysParamsService;
    private final DeviceService deviceService;
    private final ModelConfigService modelConfigService;
    private final AgentService agentService;
    private final AgentTemplateService agentTemplateService;
    private final RedisUtils redisUtils;
    private final TimbreService timbreService;
    private final AgentPluginMappingService agentPluginMappingService;
    private final AgentMcpAccessPointService agentMcpAccessPointService;
    private final AgentContextProviderService agentContextProviderService;
    private final VoiceCloneService cloneVoiceService;
    private final AgentVoicePrintDao agentVoicePrintDao;
    private final CorrectWordFileService correctWordFileService;

    @Override
    public Map<String, Object> getConfig(Boolean isCache) {
        if (isCache) {
            // Get configuration from Redis first
            Object cachedConfig = redisUtils.get(RedisKeys.getServerConfigKey());
            if (cachedConfig != null) {
                Map<String, Object> cached = JsonUtils.toStringObjectMap(cachedConfig);
                filterUnavailableOptionalConfig(cached);
                ApprovedProviderCatalog.validateRuntimeConfig(cached);
                validateCachedModelReferences(cached);
                return cached;
            }
        }

        // Build configuration
        Map<String, Object> result = new HashMap<>();
        buildConfig(result);

        // Query the default agent
        AgentTemplateEntity agent = agentTemplateService.getDefaultTemplate();
        if (agent == null) {
            throw new RenException(ErrorCode.AGENT_TEMPLATE_NOT_FOUND);
        }

        // Build module configuration
        buildModuleConfig(
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                agent.getVadModelId(),
                agent.getAsrModelId(),
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                result,
                isCache);

        filterUnavailableOptionalConfig(result);
        ApprovedProviderCatalog.validateRuntimeConfig(result);
        // Cache configuration in Redis
        redisUtils.set(RedisKeys.getServerConfigKey(), result);

        return result;
    }

    @Override
    public Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule) {
        // Check whether this is a management console request
        String redisKey = RedisKeys.getTmpRegisterMacKey(macAddress);
        Object isAdminRequest = redisUtils.get(redisKey);

        if (isAdminRequest != null && "true".equals(isAdminRequest)) {
            // For management console requests, return getConfig results
            redisUtils.delete(redisKey); // Clean up after use
            return getConfig(true);
        }
        // Find a device by MAC address
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            // Check Redis for a device awaiting connection
            String cachedCode = deviceService.geCodeByDeviceId(macAddress);
            if (StringUtils.isNotBlank(cachedCode)) {
                throw new RenException(ErrorCode.OTA_DEVICE_NEED_BIND, cachedCode);
            }
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND);
        }

        // Get agent information
        AgentEntity agent = agentService.getAgentById(device.getAgentId());
        if (agent == null) {
            throw new RenException(ErrorCode.AGENT_NOT_FOUND);
        }
        // Validate even VAD/ASR that the caller claims to have already instantiated.
        ApprovedProviderCatalog.validateSelections(agent, modelConfigService::getModelByIdFromCache);
        modelConfigService.validateVoiceSelection(agent.getTtsModelId(), agent.getTtsVoiceId());
        // Get voice information
        String voice = null;
        String referenceAudio = null;
        String referenceText = null;
        String language = null;
        TimbreDetailsVO timbre = timbreService.get(agent.getTtsVoiceId());
        if (timbre != null) {
            voice = timbre.getTtsVoice();
            referenceAudio = timbre.getReferenceAudio();
            referenceText = timbre.getReferenceText();
            // Prefer the user-selected language; otherwise use the voice's first supported language
            if (StringUtils.isNotBlank(agent.getTtsLanguage())) {
                language = agent.getTtsLanguage();
            } else if (StringUtils.isNotBlank(timbre.getLanguages())) {
                language = timbre.getLanguages().split("、")[0].trim();
            }
        } else if (StringUtils.isNotBlank(agent.getTtsVoiceId())) {
            throw ApprovedProviderCatalog.unavailable("tts");
        }
        // Build response data
        Map<String, Object> result = new HashMap<>();
        // Get the maximum daily output character count per device
        String deviceMaxOutputSize = sysParamsService.getValue("device_max_output_size", true);
        result.put("device_max_output_size", deviceMaxOutputSize);

        // Get chat history configuration
        Integer chatHistoryConf = agent.getChatHistoryConf();
        if (agent.getMemModelId() != null && agent.getMemModelId().equals(Constant.MEMORY_NO_MEM)) {
            chatHistoryConf = Constant.ChatHistoryConfEnum.IGNORE.getCode();
        } else if (agent.getMemModelId() != null
                && !agent.getMemModelId().equals(Constant.MEMORY_NO_MEM)
                && agent.getChatHistoryConf() == null) {
            chatHistoryConf = Constant.ChatHistoryConfEnum.RECORD_TEXT_AUDIO.getCode();
        }
        result.put("chat_history_conf", chatHistoryConf);
        // Omit models already instantiated by the client
        String alreadySelectedVadModelId = selectedModule.get("VAD");
        if (alreadySelectedVadModelId != null && alreadySelectedVadModelId.equals(agent.getVadModelId())) {
            agent.setVadModelId(null);
        }
        String alreadySelectedAsrModelId = selectedModule.get("ASR");
        if (alreadySelectedAsrModelId != null && alreadySelectedAsrModelId.equals(agent.getAsrModelId())) {
            agent.setAsrModelId(null);
        }

        // Add function calling parameters
        if (!Objects.equals(agent.getIntentModelId(), "Intent_nointent")) {
            String agentId = agent.getId();
            List<AgentPluginMapping> pluginMappings = agentPluginMappingService.agentPluginParamsByAgentId(agentId);
            if (pluginMappings != null && !pluginMappings.isEmpty()) {
                Map<String, Object> pluginParams = new HashMap<>();
                for (AgentPluginMapping pluginMapping : pluginMappings) {
                    if (!ApprovedProviderCatalog.isSupportedPlugin(pluginMapping.getProviderCode())) continue;
                    pluginParams.put(pluginMapping.getProviderCode(), pluginMapping.getParamInfo());
                }
                result.put("plugins", pluginParams);
            }
        }
        // Get the MCP access point URL
        String mcpEndpoint = agentMcpAccessPointService.getAgentMcpAccessAddress(agent.getId());
        if (StringUtils.isNotBlank(mcpEndpoint) && mcpEndpoint.startsWith("ws")) {
            mcpEndpoint = mcpEndpoint.replace("/mcp/", "/call/");
            result.put("mcp_endpoint", mcpEndpoint);
        }

        // Get context source configuration
        AgentContextProviderEntity contextProviderEntity = agentContextProviderService.getByAgentId(agent.getId());
        if (contextProviderEntity != null && contextProviderEntity.getContextProviders() != null
                && !contextProviderEntity.getContextProviders().isEmpty()) {
            result.put("context_providers", contextProviderEntity.getContextProviders());
        }

        // Get voiceprint information
        buildVoiceprintConfig(agent.getId(), result);

        // Build module configuration
        buildModuleConfig(
                agent.getAgentName(),
                agent.getSystemPrompt(),
                agent.getSummaryMemory(),
                voice,
                referenceAudio,
                referenceText,
                language,
                agent.getTtsVolume(),
                agent.getTtsRate(),
                agent.getTtsPitch(),
                agent.getVadModelId(),
                agent.getAsrModelId(),
                agent.getLlmModelId(),
                agent.getVllmModelId(),
                agent.getSlmModelId(),
                agent.getTtsModelId(),
                agent.getMemModelId(),
                agent.getIntentModelId(),
                null,
                result,
                true);

        filterUnavailableOptionalConfig(result);
        ApprovedProviderCatalog.validateRuntimeConfig(result);
        return result;
    }

    private void validateCachedModelReferences(Map<String, Object> config) {
        for (var branch : config.entrySet()) {
            String role = ApprovedProviderCatalog.normalize(branch.getKey());
            if (role.equals("slm")) role = "llm";
            if (!List.of("vad", "asr", "llm", "vllm", "tts", "memory", "intent", "rag").contains(role)) continue;
            if (!(branch.getValue() instanceof Map<?, ?> models)) throw ApprovedProviderCatalog.unavailable(role);
            for (Object id : models.keySet()) {
                ApprovedProviderCatalog.validateSelection(role, modelConfigService.getModelByIdFromCache(String.valueOf(id)));
            }
        }
    }

    /** Historical optional settings become inert without blocking the core configuration. */
    private void filterUnavailableOptionalConfig(Map<String, Object> config) {
        Object plugins = config.get("plugins");
        if (plugins instanceof Map<?, ?> entries) {
            Map<String, Object> permitted = new HashMap<>();
            for (var entry : entries.entrySet()) {
                try {
                    String code = String.valueOf(entry.getKey());
                    ApprovedProviderCatalog.validateRuntimeConfig(Map.of("plugins", Map.of(code, entry.getValue())));
                    permitted.put(code, entry.getValue());
                } catch (RuntimeException unavailable) { /* No credentials or unsafe URL leave this boundary. */ }
            }
            config.put("plugins", permitted);
        }
        Object contexts = config.get("context_providers");
        if (contexts instanceof Iterable<?> providers) {
            List<Object> permitted = new ArrayList<>();
            for (Object provider : providers) {
                try {
                    ApprovedProviderCatalog.validateRuntimeConfig(Map.of("context_providers", List.of(provider)));
                    permitted.add(provider);
                } catch (RuntimeException unavailable) { /* Optional stale context is unavailable. */ }
            }
            config.put("context_providers", permitted);
        }
        for (String optional : List.of("mcp_endpoint", "voiceprint")) {
            Object value = config.get(optional);
            if (value == null) continue;
            try { ApprovedProviderCatalog.validateRuntimeConfig(Map.of(optional, value)); }
            catch (RuntimeException unavailable) { config.remove(optional); }
        }
        Object server = config.get("server");
        if (server instanceof Map<?, ?> values && values.get("voice_print") != null) {
            try {
                xiaozhi.common.utils.ApprovedServicePolicy.validateEndpoint(String.valueOf(values.get("voice_print")), "voiceprint");
            } catch (RuntimeException unavailable) {
                Map<String, Object> safe = JsonUtils.toStringObjectMap(values);
                safe.remove("voice_print");
                config.put("server", safe);
            }
        }
    }

    @Override
    public List<String> getCorrectWords(String macAddress) {
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            return Collections.emptyList();
        }
        List<CorrectWordSimpleVO> items = correctWordFileService.getAllItemsByAgentId(device.getAgentId());
        return items.stream()
                .map(item -> item.getSourceWord() + "|" + item.getTargetWord())
                .collect(Collectors.toList());
    }

    /**
     * Build configuration
     * 
     * @param config system parameter list
     * @return configuration
     */
    private Object buildConfig(Map<String, Object> config) {

        // Query all system parameters
        List<SysParamsDTO> paramsList = sysParamsService.list(new HashMap<>());

        for (SysParamsDTO param : paramsList) {
            String[] keys = param.getParamCode().split("\\.");
            if (keys.length > 1 && "plugins".equals(keys[0])
                    && !ApprovedProviderCatalog.isSupportedPluginConfig(keys[1])) continue;
            Map<String, Object> current = config;

            // Traverse all keys except the last
            for (int i = 0; i < keys.length - 1; i++) {
                String key = keys[i];
                Object nestedConfig = current.computeIfAbsent(key, ignored -> new HashMap<String, Object>());
                Map<String, Object> nestedMap = JsonUtils.toStringObjectMap(nestedConfig);
                current.put(key, nestedMap);
                current = nestedMap;
            }

            // Process the last key
            String lastKey = keys[keys.length - 1];
            String value = param.getParamValue();

            // Convert the value according to valueType
            switch (param.getValueType().toLowerCase()) {
                case "number":
                    try {
                        double doubleValue = Double.parseDouble(value);
                        // Convert integer-form numeric values to Integer
                        if (doubleValue == (int) doubleValue) {
                            current.put(lastKey, (int) doubleValue);
                        } else {
                            current.put(lastKey, doubleValue);
                        }
                    } catch (NumberFormatException e) {
                        current.put(lastKey, value);
                    }
                    break;
                case "boolean":
                    current.put(lastKey, Boolean.parseBoolean(value));
                    break;
                case "array":
                    // Convert a semicolon-separated string to a numeric array
                    List<String> list = new ArrayList<>();
                    for (String num : value.split(";")) {
                        if (StringUtils.isNotBlank(num)) {
                            list.add(num.trim());
                        }
                    }
                    current.put(lastKey, list);
                    break;
                case "json":
                    try {
                        current.put(lastKey, JsonUtils.parseObject(value, Object.class));
                    } catch (Exception e) {
                        current.put(lastKey, value);
                    }
                    break;
                default:
                    current.put(lastKey, value);
            }
        }

        return config;
    }

    /**
     * Build voiceprint configuration
     * 
     * @param agentId agent ID
     * @param result result map
     */
    private void buildVoiceprintConfig(String agentId, Map<String, Object> result) {
        try {
            // Get the voiceprint API URL
            String voiceprintUrl = sysParamsService.getValue(Constant.SERVER_VOICE_PRINT, true);
            if (StringUtils.isBlank(voiceprintUrl) || "null".equals(voiceprintUrl)) {
                return;
            }
            xiaozhi.common.utils.ApprovedServicePolicy.validateEndpoint(voiceprintUrl, "voiceprint");

            // Get the agent's voiceprints without user permission validation
            List<AgentVoicePrintVO> voiceprints = getVoiceprintsByAgentId(agentId);
            if (voiceprints == null || voiceprints.isEmpty()) {
                return;
            }

            // Build the speakers list
            List<String> speakers = new ArrayList<>();
            for (AgentVoicePrintVO voiceprint : voiceprints) {
                String speakerStr = String.format("%s,%s,%s",
                        voiceprint.getId(),
                        voiceprint.getSourceName(),
                        voiceprint.getIntroduce() != null ? voiceprint.getIntroduce() : "");
                speakers.add(speakerStr);
            }

            // Build voiceprint configuration
            Map<String, Object> voiceprintConfig = new HashMap<>();
            voiceprintConfig.put("url", voiceprintUrl);
            voiceprintConfig.put("speakers", speakers);

            // Get the recognition similarity threshold, defaulting to 0.4
            String thresholdStr = sysParamsService.getValue("server.voiceprint_similarity_threshold", true);
            if (StringUtils.isNotBlank(thresholdStr) && !"null".equals(thresholdStr)) {
                try {
                    double threshold = Double.parseDouble(thresholdStr);
                    voiceprintConfig.put("similarity_threshold", threshold);
                } catch (NumberFormatException e) {
                    // Use 0.4 if parsing fails
                    voiceprintConfig.put("similarity_threshold", 0.4);
                }
            } else {
                voiceprintConfig.put("similarity_threshold", 0.4);
            }

            result.put("voiceprint", voiceprintConfig);
        } catch (Exception e) {
            // Failure to get voiceprint configuration must not affect other features
            System.err.println("Optional voiceprint configuration unavailable; endpoint details withheld");
        }
    }

    /**
     * Get voiceprints associated with the agent
     * 
     * @param agentId agent ID
     * @return voiceprint information list
     */
    private List<AgentVoicePrintVO> getVoiceprintsByAgentId(String agentId) {
        LambdaQueryWrapper<AgentVoicePrintEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(AgentVoicePrintEntity::getAgentId, agentId);
        queryWrapper.orderByAsc(AgentVoicePrintEntity::getCreateDate);
        List<AgentVoicePrintEntity> entities = agentVoicePrintDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(entities, AgentVoicePrintVO.class);
    }

    /**
     * Build module configuration
     * 
     * @param prompt prompt
     * @param voice voice
     * @param referenceAudio reference audio path
     * @param referenceText reference text
     * @param vadModelId VAD model ID
     * @param asrModelId ASR model ID
     * @param llmModelId LLM model ID
     * @param ttsModelId TTS model ID
     * @param memModelId memory model ID
     * @param intentModelId intent model ID
     * @param result result map
     */
    private void buildModuleConfig(
            String assistantName,
            String prompt,
            String summaryMemory,
            String voice,
            String referenceAudio,
            String referenceText,
            String language,
            Integer ttsVolume,
            Integer ttsRate,
            Integer ttsPitch,
            String vadModelId,
            String asrModelId,
            String llmModelId,
            String vllmModelId,
            String slmModelId,
            String ttsModelId,
            String memModelId,
            String intentModelId,
            String ragModelId,
            Map<String, Object> result,
            boolean isCache) {
        Map<String, String> selectedModule = new HashMap<>();

        String[] modelTypes = { "VAD", "ASR", "TTS", "Memory", "Intent", "LLM", "VLLM", "SLM", "RAG" };
        String[] modelIds = { vadModelId, asrModelId, ttsModelId, memModelId, intentModelId, llmModelId, vllmModelId,
                slmModelId, ragModelId };
        String intentLLMModelId = null;
        String memLocalShortLLMModelId = null;

        for (int i = 0; i < modelIds.length; i++) {
            if (modelIds[i] == null) {
                continue;
            }
            // Important: pass false as the third argument to retrieve the original secret
            ModelConfigEntity model = modelConfigService.getModelByIdFromCache(modelIds[i]);
            if (model == null) {
                throw ApprovedProviderCatalog.unavailable(modelTypes[i]);
            }
            ApprovedProviderCatalog.validateSelection("SLM".equals(modelTypes[i]) ? "llm" : modelTypes[i], model);
            // Runtime decorations must not mutate shared cached entities.
            model = ConvertUtils.sourceToTarget(model, ModelConfigEntity.class);
            model.setConfigJson(new cn.hutool.json.JSONObject(model.getConfigJson().toString()));
            Map<String, Object> typeConfig = new HashMap<>();
            if (model.getConfigJson() != null) {
                typeConfig.put(model.getId(), model.getConfigJson());
                // Add private_voice for TTS types
                if ("TTS".equals(modelTypes[i])) {
                    if (voice != null)
                        ((Map<String, Object>) model.getConfigJson()).put("private_voice", voice);
                    if (referenceAudio != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ref_audio", referenceAudio);
                    if (referenceText != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ref_text", referenceText);
                    if (language != null)
                        ((Map<String, Object>) model.getConfigJson()).put("language", language);
                    if (ttsVolume != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ttsVolume", ttsVolume);
                    if (ttsRate != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ttsRate", ttsRate);
                    if (ttsPitch != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ttsPitch", ttsPitch);

                }
                // For Intent with type=intent_llm, add the auxiliary model
                if ("Intent".equals(modelTypes[i])) {
                    Map<String, Object> map = (Map<String, Object>) model.getConfigJson();
                    if ("intent_llm".equals(map.get("type"))) {
                        intentLLMModelId = (String) map.get("llm");
                        if (StringUtils.isNotBlank(intentLLMModelId) && intentLLMModelId.equals(llmModelId)) {
                            intentLLMModelId = null;
                        }
                    }
                    if (map.get("functions") != null) {
                        Object configuredFunctions = map.get("functions");
                        if (configuredFunctions instanceof String functionStr && StringUtils.isNotBlank(functionStr)) {
                            String[] functions = functionStr.split(";");
                            map.put("functions", functions);
                        }
                    }
                }
                if ("Memory".equals(modelTypes[i])) {
                    Map<String, Object> map = (Map<String, Object>) model.getConfigJson();
                    if ("mem_local_short".equals(map.get("type"))) {
                        memLocalShortLLMModelId = (String) map.get("llm");
                        if (StringUtils.isNotBlank(memLocalShortLLMModelId)
                                && memLocalShortLLMModelId.equals(llmModelId)) {
                            memLocalShortLLMModelId = null;
                        }
                    }
                }
                // For LLM with a nonempty intentLLMModelId, add the auxiliary model
                if ("LLM".equals(modelTypes[i])) {
                    if (StringUtils.isNotBlank(intentLLMModelId)) {
                        if (!typeConfig.containsKey(intentLLMModelId)) {
                            // Add isMaskSensitive=false here
                            ModelConfigEntity intentLLM = modelConfigService.getModelByIdFromCache(intentLLMModelId);
                            ApprovedProviderCatalog.validateSelection("llm", intentLLM);
                            typeConfig.put(intentLLM.getId(), intentLLM.getConfigJson());
                        }
                    }
                    if (StringUtils.isNotBlank(memLocalShortLLMModelId)) {
                        if (!typeConfig.containsKey(memLocalShortLLMModelId)) {
                            // Add isMaskSensitive=false here
                            ModelConfigEntity memLocalShortLLM = modelConfigService
                                    .getModelByIdFromCache(memLocalShortLLMModelId);
                            ApprovedProviderCatalog.validateSelection("llm", memLocalShortLLM);
                            typeConfig.put(memLocalShortLLM.getId(), memLocalShortLLM.getConfigJson());
                        }
                    }
                    // Also return the selected SLM for the LLM, avoiding duplicates with the same ID
                    if (StringUtils.isNotBlank(slmModelId) && !slmModelId.equals(llmModelId)) {
                        if (!typeConfig.containsKey(slmModelId)) {
                            ModelConfigEntity slmModel = modelConfigService.getModelByIdFromCache(slmModelId);
                            ApprovedProviderCatalog.validateSelection("llm", slmModel);
                            if (slmModel != null && slmModel.getConfigJson() != null) {
                                typeConfig.put(slmModel.getId(), slmModel.getConfigJson());
                            }
                        }
                    }
                }
            }
            result.put(modelTypes[i], typeConfig);

            selectedModule.put(modelTypes[i], model.getId());
        }

        result.put("selected_module", selectedModule);
        if (StringUtils.isNotBlank(prompt)) {
            // Preserve the Chinese proper name Xiaozhi in the assistant-name fallback.
            prompt = prompt.replace("{{assistant_name}}", StringUtils.isBlank(assistantName) ? "小智" : assistantName);
        }
        result.put("prompt", prompt);
        result.put("summaryMemory", summaryMemory);
    }
}
