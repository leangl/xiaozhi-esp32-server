package xiaozhi.modules.model.service.impl;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.incrementer.DefaultIdentifierGenerator;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.metadata.OrderItem;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.json.JSONObject;
import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import xiaozhi.common.utils.SensitiveDataUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.dto.LlmModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelConfigBodyDTO;
import xiaozhi.modules.model.dto.ModelConfigDTO;
import xiaozhi.modules.model.dto.ModelProviderDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.model.service.ModelProviderService;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.timbre.dao.TimbreDao;

@Service
@AllArgsConstructor
@Slf4j
public class ModelConfigServiceImpl extends BaseServiceImpl<ModelConfigDao, ModelConfigEntity>
        implements ModelConfigService {

    private final ModelConfigDao modelConfigDao;
    private final ModelProviderService modelProviderService;
    private final RedisUtils redisUtils;
    private final AgentDao agentDao;
    private final TimbreDao timbreDao;

    @Override
    public void validateVoiceSelection(String ttsModelId, String voiceId) {
        if (StringUtils.isBlank(voiceId)) return;
        requireSelectable(ttsModelId, "tts");
        var voice = timbreDao.selectById(voiceId);
        if (voice == null || !java.util.Objects.equals(ttsModelId, voice.getTtsModelId())) {
            throw ApprovedProviderCatalog.unavailable("tts");
        }
    }

    @Override
    public List<ModelBasicInfoDTO> getModelCodeList(String modelType, String modelName) {
        List<ModelConfigEntity> entities = modelConfigDao.selectList(
                new QueryWrapper<ModelConfigEntity>()
                        .eq("model_type", modelType)
                        .eq("is_enabled", 1)
                        .like(StringUtils.isNotBlank(modelName), "model_name", modelName)
                        .orderByAsc("sort"));
        return ConvertUtils.sourceToTarget(entities.stream().filter(ApprovedProviderCatalog::isAvailable).toList(), ModelBasicInfoDTO.class);
    }

    @Override
    public List<LlmModelBasicInfoDTO> getLlmModelCodeList(String modelName) {
        List<ModelConfigEntity> entities = modelConfigDao.selectList(
                new QueryWrapper<ModelConfigEntity>()
                        .eq("model_type", "llm")
                        .eq("is_enabled", 1)
                        .like(StringUtils.isNotBlank(modelName), "model_name", modelName));

        return entities.stream().filter(ApprovedProviderCatalog::isAvailable).map(item -> {
            LlmModelBasicInfoDTO dto = new LlmModelBasicInfoDTO();
            dto.setId(item.getId());
            dto.setModelName(item.getModelName());
            String type = item.getConfigJson().getOrDefault("type", "").toString();
            dto.setType(type);
            return dto;
        }).toList();
    }

    @Override
    public PageData<ModelConfigDTO> getPageList(String modelType, String modelName, String page, String limit) {
        Map<String, Object> params = new HashMap<>();
        params.put(Constant.PAGE, page);
        params.put(Constant.LIMIT, limit);

        long curPage = Long.parseLong(page);
        long pageSize = Long.parseLong(limit);
        Page<ModelConfigEntity> pageInfo = new Page<>(curPage, pageSize);

        // Sort by is_enabled descending, then sort ascending
        pageInfo.addOrder(OrderItem.desc("is_enabled"), OrderItem.asc("sort"));

        IPage<ModelConfigEntity> modelConfigEntityIPage = modelConfigDao.selectPage(
                pageInfo,
                new QueryWrapper<ModelConfigEntity>()
                        .eq("model_type", modelType)
                        .like(StringUtils.isNotBlank(modelName), "model_name", modelName));

        return getPageData(modelConfigEntityIPage, ModelConfigDTO.class);
    }

    @Override
    public ModelConfigDTO edit(String modelType, String provideCode, String id, ModelConfigBodyDTO modelConfigBodyDTO) {
        // 1. Validate parameters
        validateEditParameters(modelType, provideCode, id, modelConfigBodyDTO);

        // 2. Validate the model provider
        validateModelProvider(modelType, provideCode);

        // 3. Get original configuration without masking sensitive data
        ModelConfigEntity originalEntity = getOriginalConfigFromDb(id);

        // 5. Prepare the update entity and handle sensitive data
        ModelConfigEntity modelConfigEntity = prepareUpdateEntity(modelConfigBodyDTO, originalEntity, modelType, id);

        ApprovedProviderCatalog.validate(modelType, provideCode, modelConfigEntity.getConfigJson());
        validateCredentialReuse(originalEntity, modelConfigEntity, modelConfigBodyDTO.getConfigJson());
        validateLlmConfiguration(modelConfigEntity.getConfigJson());

        // 6. Update the database
        modelConfigDao.updateById(modelConfigEntity);

        // 7. Clear the cache
        clearModelCache(id);

        // 8. Return processed data with sensitive fields masked
        return buildResponseDTO(modelConfigEntity);
    }

    @Override
    public ModelConfigDTO add(String modelType, String provideCode, ModelConfigBodyDTO modelConfigBodyDTO) {
        validateAddParameters(modelType, provideCode, modelConfigBodyDTO);

        validateModelProvider(modelType, provideCode);

        ModelConfigEntity modelConfigEntity = prepareAddEntity(modelConfigBodyDTO, modelType);

        ApprovedProviderCatalog.validate(modelType, provideCode, modelConfigEntity.getConfigJson());
        validateLlmConfiguration(modelConfigEntity.getConfigJson());

        modelConfigDao.insert(modelConfigEntity);
        redisUtils.delete(RedisKeys.getServerConfigKey());

        return buildResponseDTO(modelConfigEntity);
    }

    @Override
    public void delete(String id) {
        if (StringUtils.isBlank(id)) {
            throw new RenException(ErrorCode.IDENTIFIER_NOT_NULL);
        }

        ModelConfigEntity modelConfig = modelConfigDao.selectById(id);
        if (modelConfig != null && modelConfig.getIsDefault() == 1) {
            throw new RenException(ErrorCode.DEFAULT_MODEL_DELETE_ERROR);
        }

        checkAgentReference(id);
        checkIntentConfigReference(id);

        modelConfigDao.deleteById(id);

        clearModelCache(id);
    }

    @Override
    public String getModelNameById(String id) {
        if (StringUtils.isBlank(id)) {
            return null;
        }

        String cacheKey = RedisKeys.getModelNameById(id);
        String cachedName = (String) redisUtils.get(cacheKey);
        if (StringUtils.isNotBlank(cachedName)) {
            return cachedName;
        }

        ModelConfigEntity entity = modelConfigDao.selectById(id);
        if (entity != null) {
            String modelName = entity.getModelName();
            if (StringUtils.isNotBlank(modelName)) {
                redisUtils.set(cacheKey, modelName);
            }
            return modelName;
        }

        return null;
    }

    @Override
    public ModelConfigEntity selectById(Serializable id) {
        ModelConfigEntity entity = modelConfigDao.selectById(id);
        if (entity != null && entity.getConfigJson() != null) {
            entity = redactedForManagement(entity);
        }
        return entity;
    }

    @Override
    protected <D> PageData<D> getPageData(IPage<?> page, Class<D> target) {
        List<?> records = page.getRecords();
        if (records != null && !records.isEmpty()) {
            for (Object record : records) {
                if (record instanceof ModelConfigEntity) {
                    ModelConfigEntity entity = (ModelConfigEntity) record;
                    ModelConfigEntity safe = redactedForManagement(entity);
                    entity.setConfigJson(safe.getConfigJson());
                    entity.setIsEnabled(safe.getIsEnabled());
                }
            }
        }
        return super.getPageData(page, target);
    }

    @Override
    public ModelConfigEntity getModelByIdFromCache(String id) {
        if (StringUtils.isBlank(id)) {
            return null;
        }
        String cacheKey = RedisKeys.getModelConfigById(id);
        ModelConfigEntity entity = (ModelConfigEntity) redisUtils.get(cacheKey);
        if (entity == null) {
            entity = modelConfigDao.selectById(id);
            if (entity != null) {
                if (!ApprovedProviderCatalog.isAvailable(entity)) throw ApprovedProviderCatalog.unavailable(entity.getModelType());
                redisUtils.set(cacheKey, entity);
            }
        }
        if (entity != null && !ApprovedProviderCatalog.isAvailable(entity)) throw ApprovedProviderCatalog.unavailable(entity.getModelType());
        if (entity == null) return null;
        ModelConfigEntity result = ConvertUtils.sourceToTarget(entity, ModelConfigEntity.class);
        result.setConfigJson(new JSONObject(entity.getConfigJson().toString()));
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(ModelConfigEntity entity) {
        ApprovedProviderCatalog.validate(entity);
        validateLlmConfiguration(entity.getConfigJson());
        boolean inserted = modelConfigDao.insert(entity) > 0;
        if (inserted) redisUtils.delete(RedisKeys.getServerConfigKey());
        return inserted;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(ModelConfigEntity entity) {
        ModelConfigEntity original = getOriginalConfigFromDb(entity.getId());
        ModelConfigEntity effective = ConvertUtils.sourceToTarget(original, ModelConfigEntity.class);
        if (entity.getModelType() != null) effective.setModelType(entity.getModelType());
        if (entity.getConfigJson() != null) effective.setConfigJson(entity.getConfigJson());
        if (entity.getIsEnabled() != null) effective.setIsEnabled(entity.getIsEnabled());
        // Disabling a stale row is safe; activating or replacing configuration is not.
        if (!Integer.valueOf(0).equals(entity.getIsEnabled()) || entity.getConfigJson() != null) {
            ApprovedProviderCatalog.validate(effective);
            validateLlmConfiguration(effective.getConfigJson());
            validateCredentialReuse(original, effective, entity.getConfigJson());
        }
        boolean updated = modelConfigDao.updateById(entity) > 0;
        if (updated) clearModelCache(entity.getId());
        return updated;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<ModelConfigEntity> entities, int batchSize) {
        entities.forEach(entity -> {
            ApprovedProviderCatalog.validate(entity);
            validateLlmConfiguration(entity.getConfigJson());
        });
        boolean inserted = super.insertBatch(entities, batchSize);
        if (inserted) redisUtils.delete(RedisKeys.getServerConfigKey());
        return inserted;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<ModelConfigEntity> entities, int batchSize) {
        // Validate the complete batch before any SQL is issued by the batch executor.
        for (ModelConfigEntity update : entities) {
            ModelConfigEntity original = getOriginalConfigFromDb(update.getId());
            ModelConfigEntity prior = ConvertUtils.sourceToTarget(original, ModelConfigEntity.class);
            if (update.getModelType() != null) prior.setModelType(update.getModelType());
            if (update.getConfigJson() != null) prior.setConfigJson(update.getConfigJson());
            if (!Integer.valueOf(0).equals(update.getIsEnabled()) || update.getConfigJson() != null) {
                ApprovedProviderCatalog.validate(prior);
                validateLlmConfiguration(prior.getConfigJson());
                validateCredentialReuse(original, prior, update.getConfigJson());
            }
        }
        boolean updated = super.updateBatchById(entities, batchSize);
        if (updated) entities.forEach(entity -> clearModelCache(entity.getId()));
        return updated;
    }

    private void validateCredentialReuse(ModelConfigEntity prior, ModelConfigEntity next, JSONObject submitted) {
        JSONObject original = prior.getConfigJson();
        if (original == null) return;
        JSONObject effective = next.getConfigJson();
        boolean recipientChanged = !ApprovedProviderCatalog.normalize(original.getStr("type"))
                .equals(ApprovedProviderCatalog.normalize(effective.getStr("type")));
        for (String key : List.of("base_url", "api_url", "url", "endpoint", "host")) {
            if (!java.util.Objects.equals(original.get(key), effective.get(key))) recipientChanged = true;
        }
        if (!recipientChanged) return;
        for (String key : original.keySet()) {
            if (SensitiveDataUtils.isSensitiveField(key) && original.get(key) != null) {
                Object replacement = submitted == null ? null : submitted.get(key);
                if (!(replacement instanceof String value) || SensitiveDataUtils.isMaskedValue(value)) {
                    throw new RenException("Provider destination changed; explicitly supply new credentials without reusing masked legacy values");
                }
            }
        }
    }

    private ModelConfigEntity redactedForManagement(ModelConfigEntity source) {
        ModelConfigEntity safe = ConvertUtils.sourceToTarget(source, ModelConfigEntity.class);
        if (!ApprovedProviderCatalog.isSupported(source)) {
            safe.setIsEnabled(0);
            safe.setConfigJson(new JSONObject().set("unavailable", true)
                    .set("reason", "Select a supported provider with a reviewed endpoint"));
        } else if (source.getConfigJson() != null) {
            safe.setConfigJson(maskSensitiveFields(source.getConfigJson()));
        }
        return safe;
    }

    /**
     * Validate update parameters
     */
    private void validateEditParameters(String modelType, String provideCode, String id,
            ModelConfigBodyDTO modelConfigBodyDTO) {
        if (StringUtils.isBlank(modelType) || StringUtils.isBlank(provideCode)) {
            throw new RenException(ErrorCode.MODEL_TYPE_PROVIDE_CODE_NOT_NULL);
        }
        if (StringUtils.isBlank(id)) {
            throw new RenException(ErrorCode.IDENTIFIER_NOT_NULL);
        }
        if (modelConfigBodyDTO == null) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
    }

    /**
     * Validate creation parameters
     */
    private void validateAddParameters(String modelType, String provideCode, ModelConfigBodyDTO modelConfigBodyDTO) {
        if (StringUtils.isBlank(modelType) || StringUtils.isBlank(provideCode)) {
            throw new RenException(ErrorCode.MODEL_TYPE_PROVIDE_CODE_NOT_NULL);
        }
        if (modelConfigBodyDTO == null) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
        if (StringUtils.isBlank(modelConfigBodyDTO.getId())) {
            // Follow the MP @TableId AutoUUID strategy
            // com.baomidou.mybatisplus.core.incrementer.DefaultIdentifierGenerator(UUID.replace("-",""))
            // Assign the default model ID
            modelConfigBodyDTO.setId(DefaultIdentifierGenerator.getInstance().nextUUID(ModelConfigEntity.class));
        }
    }

    /**
     * Set the default model
     */
    @Override
    public void setDefaultModel(String modelType, int isDefault) {
        // Parameter validation
        if (StringUtils.isBlank(modelType)) {
            throw new RenException(ErrorCode.MODEL_TYPE_PROVIDE_CODE_NOT_NULL);
        }

        ModelConfigEntity entity = new ModelConfigEntity();
        entity.setIsDefault(isDefault);
        modelConfigDao.update(entity, new QueryWrapper<ModelConfigEntity>()
                .eq("model_type", modelType));

        // Clear related caches
        clearModelCacheByType(modelType);
    }

    /**
     * Validate the model provider
     */
    private void validateModelProvider(String modelType, String provideCode) {
        if (!ApprovedProviderCatalog.isSupportedType(modelType, provideCode)) throw ApprovedProviderCatalog.unavailable(modelType);
        List<ModelProviderDTO> providerList = modelProviderService.getList(modelType, provideCode);
        if (CollectionUtil.isEmpty(providerList)) {
            throw new RenException(ErrorCode.MODEL_PROVIDER_NOT_EXIST);
        }
    }

    /**
     * Get original configuration from the database without sensitive data masking
     */
    private ModelConfigEntity getOriginalConfigFromDb(String id) {
        ModelConfigEntity originalEntity = modelConfigDao.selectById(id);
        if (originalEntity == null) {
            throw new RenException(ErrorCode.RESOURCE_NOT_FOUND);
        }
        return originalEntity;
    }

    /**
     * Validate LLM configuration
     */
    private void validateLlmConfiguration(JSONObject configuration) {
        if (configuration != null && StringUtils.isNotBlank(configuration.getStr("llm"))) {
            String llm = configuration.getStr("llm");
            ModelConfigEntity modelConfigEntity = modelConfigDao.selectOne(new LambdaQueryWrapper<ModelConfigEntity>()
                    .eq(ModelConfigEntity::getId, llm));

            if (modelConfigEntity == null) {
                throw new RenException(ErrorCode.LLM_NOT_EXIST);
            }

            ApprovedProviderCatalog.validateSelection("llm", modelConfigEntity);

            String modelType = modelConfigEntity.getModelType();
            if (modelType == null || !"LLM".equals(modelType.toUpperCase())) {
                throw new RenException(ErrorCode.LLM_NOT_EXIST);
            }

            // Validate the LLM type
            JSONObject configJson = modelConfigEntity.getConfigJson();
            if (configJson != null && configJson.containsKey("type")) {
                String type = ApprovedProviderCatalog.normalize(configJson.get("type").toString());
                if (!"openai".equals(type) && !"ollama".equals(type)) {
                    throw new RenException(ErrorCode.INVALID_LLM_TYPE);
                }
            }
        }
    }

    /**
     * Prepare the update entity and handle sensitive data
     */
    private ModelConfigEntity prepareUpdateEntity(ModelConfigBodyDTO modelConfigBodyDTO,
            ModelConfigEntity originalEntity,
            String modelType,
            String id) {
        // 1. Copy the original entity, preserving all data including sensitive fields
        ModelConfigEntity modelConfigEntity = ConvertUtils.sourceToTarget(originalEntity, ModelConfigEntity.class);
        modelConfigEntity.setId(id);
        modelConfigEntity.setModelType(modelType);

        // 2. Update non-sensitive fields only
        modelConfigEntity.setModelName(modelConfigBodyDTO.getModelName());
        modelConfigEntity.setSort(modelConfigBodyDTO.getSort());
        modelConfigEntity.setIsEnabled(modelConfigBodyDTO.getIsEnabled());
        modelConfigEntity.setRemark(modelConfigBodyDTO.getRemark());
        // 3. Update configuration JSON only for non-sensitive or explicitly changed sensitive fields
        if (modelConfigBodyDTO.getConfigJson() != null && originalEntity.getConfigJson() != null) {
            JSONObject originalJson = originalEntity.getConfigJson();
            JSONObject updatedJson = new JSONObject(originalJson); // Modify the original JSON

            // Traverse updated JSON, applying non-sensitive or genuinely changed sensitive fields
            for (String key : modelConfigBodyDTO.getConfigJson().keySet()) {
                Object value = modelConfigBodyDTO.getConfigJson().get(key);

                // For sensitive fields, verify an actual change; the frontend may have sent a masked value
                if (SensitiveDataUtils.isSensitiveField(key)) {

                    if (value instanceof String && !SensitiveDataUtils.isMaskedValue((String) value)) {
                        updatedJson.set(key, value);
                    }
                } else if (value instanceof JSONObject) {
                    // Recursively process nested JSON
                    mergeJson(updatedJson, key, (JSONObject) value);
                } else {
                    // Update non-sensitive fields directly
                    updatedJson.set(key, value);
                }
            }

            // Remove non-sensitive fields absent from the new JSON
            for (String oldKey : originalJson.keySet().toArray(new String[0])) {
                if (!modelConfigBodyDTO.getConfigJson().containsKey(oldKey)
                        && !SensitiveDataUtils.isSensitiveField(oldKey)) {
                    updatedJson.remove(oldKey);
                }
            }

            modelConfigEntity.setConfigJson(updatedJson);
        } else if (modelConfigBodyDTO.getConfigJson() != null) {
            modelConfigEntity.setConfigJson(new JSONObject(modelConfigBodyDTO.getConfigJson().toString()));
        }

        return modelConfigEntity;
    }

    // Helper: detect masked values
    private boolean isMaskedValue(String value) {
        if (value == null)
            return false;
        // Check for the masking marker (***)
        return value.contains("***");
    }

    // Helper: recursively merge JSON while preserving original sensitive fields
    private void mergeJson(JSONObject original, String key, JSONObject updated) {
        // Null check
        if (original == null || updated == null) {
            log.warn("mergeJson: original or updated is null");
            return;
        }

        // Create a JSON object if the key is absent from original
        if (!original.containsKey(key)) {
            original.set(key, new JSONObject());
        }

        // Get the child object from original
        Object originalValue = original.get(key);
        JSONObject originalChild;

        // Check whether originalValue is a JSONObject
        if (originalValue instanceof JSONObject) {
            originalChild = (JSONObject) originalValue;
        } else {
            // Otherwise log a warning and create a JSON object
            log.warn("mergeJson: value for key '{}' is not a JSONObject (actual type: {}); creating a new object",
                    key, originalValue != null ? originalValue.getClass().getSimpleName() : "null");
            originalChild = new JSONObject();
            original.set(key, originalChild);
        }

        for (String childKey : updated.keySet()) {
            Object childValue = updated.get(childKey);
            if (childValue instanceof JSONObject) {
                mergeJson(originalChild, childKey, (JSONObject) childValue);
            } else {
                if (!SensitiveDataUtils.isSensitiveField(childKey) ||
                        (childValue instanceof String && !isMaskedValue((String) childValue))) {
                    originalChild.set(childKey, childValue);
                }
            }
        }

        // Remove non-sensitive child fields absent from the new JSON
        for (String oldChildKey : originalChild.keySet().toArray(new String[0])) {
            if (!updated.containsKey(oldChildKey) && !SensitiveDataUtils.isSensitiveField(oldChildKey)) {
                originalChild.remove(oldChildKey);
            }
        }
    }

    /**
     * Prepare the new entity
     */
    private ModelConfigEntity prepareAddEntity(ModelConfigBodyDTO modelConfigBodyDTO, String modelType) {
        ModelConfigEntity modelConfigEntity = ConvertUtils.sourceToTarget(modelConfigBodyDTO, ModelConfigEntity.class);
        modelConfigEntity.setModelType(modelType);
        modelConfigEntity.setIsDefault(0);
        return modelConfigEntity;
    }

    /**
     * Build the response DTO, handling sensitive data
     */
    private ModelConfigDTO buildResponseDTO(ModelConfigEntity entity) {
        ModelConfigDTO dto = ConvertUtils.sourceToTarget(entity, ModelConfigDTO.class);
        if (dto.getConfigJson() != null) {
            dto.setConfigJson(maskSensitiveFields(dto.getConfigJson()));
        }
        return dto;
    }

    /**
     * Handle sensitive fields
     */
    private JSONObject maskSensitiveFields(JSONObject configJson) {
        return SensitiveDataUtils.maskSensitiveFields(configJson);
    }

    /**
     * Clear the model cache
     */
    private void clearModelCache(String id) {
        redisUtils.delete(RedisKeys.getModelConfigById(id));
        redisUtils.delete(RedisKeys.getModelNameById(id));
        redisUtils.delete(RedisKeys.getServerConfigKey());
    }

    /**
     * Clear caches by model type
     */
    private void clearModelCacheByType(String modelType) {
        List<ModelConfigEntity> entities = modelConfigDao.selectList(
                new QueryWrapper<ModelConfigEntity>().eq("model_type", modelType));
        for (ModelConfigEntity entity : entities) {
            clearModelCache(entity.getId());
        }
    }

    /**
     * Check agent configuration references
     */
    private void checkAgentReference(String modelId) {
        List<AgentEntity> agents = agentDao.selectList(
                new QueryWrapper<AgentEntity>()
                        .eq("vad_model_id", modelId)
                        .or()
                        .eq("asr_model_id", modelId)
                        .or()
                        .eq("llm_model_id", modelId)
                        .or()
                        .eq("tts_model_id", modelId)
                        .or()
                        .eq("mem_model_id", modelId)
                        .or()
                        .eq("vllm_model_id", modelId)
                        .or()
                        .eq("intent_model_id", modelId));
        if (!agents.isEmpty()) {
            String agentNames = agents.stream()
                    .map(AgentEntity::getAgentName)
                    .collect(Collectors.joining("、"));
            throw new RenException(ErrorCode.MODEL_REFERENCED_BY_AGENT, agentNames);
        }
    }

    /**
     * Check intent recognition configuration references
     */
    private void checkIntentConfigReference(String modelId) {
        ModelConfigEntity modelConfig = modelConfigDao.selectById(modelId);
        if (modelConfig != null
                && "LLM".equals(modelConfig.getModelType() == null ? null : modelConfig.getModelType().toUpperCase())) {
            List<ModelConfigEntity> intentConfigs = modelConfigDao.selectList(
                    new QueryWrapper<ModelConfigEntity>()
                            .eq("model_type", "Intent")
                            .like("config_json", modelId));
            if (!intentConfigs.isEmpty()) {
                throw new RenException(ErrorCode.LLM_REFERENCED_BY_INTENT);
            }
        }
    }

    /**
     * Get eligible TTS platforms
     */
    @Override
    public List<Map<String, Object>> getTtsPlatformList() {
        // This endpoint lists voice-cloning platforms, not ordinary TTS models.
        // None of the retained implementations supports the removed cloning workflow.
        return List.of();
    }

    /**
     * Get all enabled model configurations by model type
     */
    @Override
    public List<ModelConfigEntity> getEnabledModelsByType(String modelType) {
        if (StringUtils.isBlank(modelType)) {
            return null;
        }

        List<ModelConfigEntity> entities = modelConfigDao.selectList(
                new QueryWrapper<ModelConfigEntity>()
                        .eq("model_type", modelType)
                        .eq("is_enabled", 1)
                        .orderByAsc("sort"));

        return entities.stream().filter(ApprovedProviderCatalog::isAvailable).toList();
    }
}
