package xiaozhi.modules.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.BeanUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.knowledge.dao.KnowledgeBaseDao;
import xiaozhi.modules.knowledge.dao.DocumentDao;
import xiaozhi.modules.knowledge.entity.DocumentEntity;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapter;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.security.user.SecurityUser;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Refactored knowledge base service implementation
 * Integrates the RAGFlow adapter and shadow database pattern
 */
@Service
@AllArgsConstructor
@Slf4j
public class KnowledgeBaseServiceImpl extends BaseServiceImpl<KnowledgeBaseDao, KnowledgeBaseEntity>
        implements KnowledgeBaseService {

    private final KnowledgeBaseDao knowledgeBaseDao;
    private final DocumentDao documentDao;
    private final ModelConfigService modelConfigService;
    private final ModelConfigDao modelConfigDao;
    private final RedisUtils redisUtils;

    @Override
    public PageData<KnowledgeBaseDTO> getPageList(KnowledgeBaseDTO knowledgeBaseDTO, Integer page, Integer limit) {
        Page<KnowledgeBaseEntity> pageInfo = new Page<>(page, limit);
        QueryWrapper<KnowledgeBaseEntity> queryWrapper = new QueryWrapper<>();

        if (knowledgeBaseDTO != null) {
            queryWrapper.like(StringUtils.isNotBlank(knowledgeBaseDTO.getName()), "name", knowledgeBaseDTO.getName());
            queryWrapper.eq(knowledgeBaseDTO.getStatus() != null, "status", knowledgeBaseDTO.getStatus());
            queryWrapper.eq("creator", knowledgeBaseDTO.getCreator());
        }
        queryWrapper.orderByDesc("created_at");

        IPage<KnowledgeBaseEntity> iPage = knowledgeBaseDao.selectPage(pageInfo, queryWrapper);
        PageData<KnowledgeBaseDTO> pageData = getPageData(iPage, KnowledgeBaseDTO.class);

        // Enrich with Document Count from RAG (Optional / Lazy)
        if (pageData != null && pageData.getList() != null) {
            pageData.getList().removeIf(dto -> {
                enrichDocumentCount(dto);
                // syncDatasetFromRAG deletes local records when it detects deletion in RAGFlow
                // datasetId is then cleared as a marker; remove the item from the list
                return dto.getDatasetId() == null;
            });
        }
        return pageData;
    }

    private void enrichDocumentCount(KnowledgeBaseDTO dto) {
        syncDatasetFromRAG(dto);
    }

    /**
     * Synchronize dataset information from RAGFlow: deletion, name/description, and document count
     * Query RAGFlow on every list refresh to reflect remote changes immediately
     */
    private void syncDatasetFromRAG(KnowledgeBaseDTO dto) {
        try {
            if (StringUtils.isBlank(dto.getDatasetId()) || StringUtils.isBlank(dto.getRagModelId())) {
                return;
            }

            KnowledgeBaseAdapter adapter = getAdapterByModelId(dto.getRagModelId());
            if (adapter == null) {
                return;
            }

            DatasetDTO.InfoVO datasetInfo = adapter.getDatasetInfo(dto.getDatasetId());
            // A null getDatasetInfo result confirms remote absence; failures throw RenException for the outer catch
            if (datasetInfo == null) {
                // Remote deletion confirmed: cascade cleanup locally
                log.info("Dataset {} is absent from RAGFlow; cleaning up locally", dto.getDatasetId());
                cleanupLocalDataset(dto.getDatasetId(), dto.getId());
                // Mark as deleted for removal from the caller's list
                dto.setDatasetId(null);
                return;
            }

            // Synchronize the name, removing the username_ prefix
            String ragflowName = datasetInfo.getName();
            if (StringUtils.isNotBlank(ragflowName)) {
                String localName = ragflowName.contains("_") ? ragflowName.substring(ragflowName.indexOf('_') + 1) : ragflowName;
                if (!localName.equals(dto.getName())) {
                    log.info("Synchronizing knowledge base name: {} -> {}", dto.getName(), localName);
                    KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(dto.getId());
                    if (entity != null) {
                        entity.setName(localName);
                        knowledgeBaseDao.updateById(entity);
                        dto.setName(localName);
                    }
                }
            }

            // Synchronize the description
            String ragflowDesc = datasetInfo.getDescription();
            String localDesc = dto.getDescription();
            boolean descChanged = (ragflowDesc == null && localDesc != null) || (ragflowDesc != null && !ragflowDesc.equals(localDesc));
            if (descChanged) {
                log.info("Synchronizing knowledge base description: datasetId={}", dto.getDatasetId());
                KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(dto.getId());
                if (entity != null) {
                    entity.setDescription(ragflowDesc);
                    knowledgeBaseDao.updateById(entity);
                    dto.setDescription(ragflowDesc);
                }
            }

            // Set document count, preserving existing behavior
            if (datasetInfo.getDocumentCount() != null) {
                dto.setDocumentCount(datasetInfo.getDocumentCount().intValue());
            }

        } catch (Exception e) {
            log.error("Failed to synchronize dataset information {}: {}", dto.getName(), e.getMessage());
            dto.setDocumentCount(0);
            dto.setErrorMessage(e.getMessage());
        }
    }

    /**
     * Cascade local cleanup after confirmed remote deletion
     * Do not call the RAGFlow deletion API
     */
    @Transactional(rollbackFor = Exception.class)
    public void cleanupLocalDataset(String datasetId, String entityId) {
        try {
            // 1. Delete shadow document records
            documentDao.delete(new QueryWrapper<DocumentEntity>().eq("dataset_id", datasetId));
            // 2. Delete plugin mappings
            knowledgeBaseDao.deletePluginMappingByKnowledgeBaseId(entityId);
            // 3. Delete the knowledge base record
            knowledgeBaseDao.deleteById(entityId);
            // 4. Clear the cache
            redisUtils.delete(RedisKeys.getKnowledgeBaseCacheKey(entityId));
            log.info("Local cascade cleanup completed: datasetId={}, entityId={}", datasetId, entityId);
        } catch (Exception e) {
            log.error("Local cascade cleanup failed: datasetId={}, entityId={}", datasetId, entityId, e);
        }
    }

    @Override
    public KnowledgeBaseDTO getById(String id) {
        KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(id);
        if (entity == null) {
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    public KnowledgeBaseDTO getByDatasetId(String datasetId) {
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
        // [Production Fix] Try dataset_id first, then primary key id, accepting either UUID from the frontend
        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>()
                        .eq("dataset_id", datasetId)
                        .or()
                        .eq("id", datasetId));
        if (entity == null) {
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseDTO save(KnowledgeBaseDTO dto) {
        // 1. Validation
        checkDuplicateName(dto.getName(), null);
        KnowledgeBaseAdapter adapter = null;

        // 2. RAG Creation
        String datasetId = null;
        try {
            // Use the system default RAG model if none is supplied
            if (StringUtils.isBlank(dto.getRagModelId())) {
                List<ModelConfigEntity> models = getRAGModels();
                if (models != null && !models.isEmpty()) {
                    dto.setRagModelId(models.get(0).getId());
                } else {
                    throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND, "No RAG model specified and no default is available");
                }
            }

            Map<String, Object> ragConfig = getValidatedRAGConfig(dto.getRagModelId());
            adapter = KnowledgeBaseAdapterFactory.getAdapter((String) ragConfig.get("type"),
                    ragConfig);

            DatasetDTO.CreateReq createReq = ConvertUtils.sourceToTarget(dto, DatasetDTO.CreateReq.class);
            createReq.setName(SecurityUser.getUser().getUsername() + "_" + dto.getName());

            DatasetDTO.InfoVO ragResponse = adapter.createDataset(createReq);
            if (ragResponse == null || StringUtils.isBlank(ragResponse.getId())) {
                throw new RenException(ErrorCode.RAG_API_ERROR, "Invalid RAG creation response: missing ID");
            }
            datasetId = ragResponse.getId();

            // 3. Local Save (Shadow)
            KnowledgeBaseEntity entity = ConvertUtils.sourceToTarget(dto, KnowledgeBaseEntity.class);

            // [Production Fix] Unify local and RAGFlow IDs to prevent /delete or /update failures caused by
            // local UUID vs RAG UUID confusion (error 10163)
            entity.setId(datasetId);
            entity.setDatasetId(datasetId);
            entity.setStatus(1); // Default Enabled

            // FULL PERSISTENCE: write back every field as required by the user
            // Read strongly typed DTO properties instead of parsing map keys manually
            entity.setTenantId(ragResponse.getTenantId());
            entity.setChunkMethod(ragResponse.getChunkMethod());
            entity.setEmbeddingModel(ragResponse.getEmbeddingModel());
            entity.setPermission(ragResponse.getPermission());

            if (StringUtils.isBlank(entity.getAvatar())) {
                entity.setAvatar(ragResponse.getAvatar());
            }

            // Parse Config (JSON)
            if (ragResponse.getParserConfig() != null) {
                entity.setParserConfig(JsonUtils.toJsonString(ragResponse.getParserConfig()));
            }

            // Numeric fields
            entity.setChunkCount(ragResponse.getChunkCount() != null ? ragResponse.getChunkCount() : 0L);
            entity.setDocumentCount(ragResponse.getDocumentCount() != null ? ragResponse.getDocumentCount() : 0L);
            entity.setTokenNum(ragResponse.getTokenNum() != null ? ragResponse.getTokenNum() : 0L);

            // Clear creator/updater so FieldMetaObjectHandler fills them from SecurityUser
            // ConvertUtils copies creator=0 from the DTO, causing strictInsertFill to skip population
            entity.setCreator(null);
            entity.setUpdater(null);

            knowledgeBaseDao.insert(entity);
            return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
        } catch (Exception e) {
            log.error("RAG creation or local persistence failed", e);
            // Attempt a best-effort RAG rollback if datasetId exists but local persistence fails
            if (StringUtils.isNotBlank(datasetId)) {
                try {
                    if (adapter != null)
                        adapter.deleteDataset(
                                DatasetDTO.BatchIdReq.builder().ids(Collections.singletonList(datasetId)).build());
                } catch (Exception rollbackEx) {
                    log.error("RAG rollback failed: {}", datasetId, rollbackEx);
                }
            }
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, "Failed to create knowledge base: " + e.getMessage());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    @SuppressWarnings("deprecation")
    public KnowledgeBaseDTO update(KnowledgeBaseDTO dto) {
        log.info("Update Service Called: ID={}, DatasetID={}", dto.getId(), dto.getDatasetId());
        KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(dto.getId());
        if (entity == null) {
            log.error("Update failed: Entity not found for ID={}", dto.getId());
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }

        checkDuplicateName(dto.getName(), dto.getId());

        // Check for dataset ID conflicts with other records
        if (StringUtils.isNotBlank(dto.getDatasetId())) {
            KnowledgeBaseEntity conflictEntity = knowledgeBaseDao.selectOne(
                    new QueryWrapper<KnowledgeBaseEntity>()
                            .eq("dataset_id", dto.getDatasetId())
                            .ne("id", dto.getId()));
            if (conflictEntity != null) {
                throw new RenException(ErrorCode.DB_RECORD_EXISTS);
            }
        }

        // RAG Update if needed
        if (StringUtils.isNotBlank(entity.getDatasetId()) && StringUtils.isNotBlank(dto.getRagModelId())) {
            try {
                // AUTO-FILL: if ragModelId is missing from the DTO (rare), try the entity's value
                if (StringUtils.isBlank(dto.getRagModelId())) {
                    dto.setRagModelId(entity.getRagModelId());
                }

                // [FIX] Fill missing key DTO fields from existing entity values
                // Ensure the RAGFlow request contains all required fields for partial update support
                if (StringUtils.isBlank(dto.getPermission())) {
                    dto.setPermission(entity.getPermission());
                }
                if (StringUtils.isBlank(dto.getChunkMethod())) {
                    dto.setChunkMethod(entity.getChunkMethod());
                }

                KnowledgeBaseAdapter adapter = getAdapterByModelId(dto.getRagModelId());
                if (adapter != null) {
                    DatasetDTO.UpdateReq updateReq = ConvertUtils.sourceToTarget(dto, DatasetDTO.UpdateReq.class);

                    // 1. Handle prefixes for required/core fields
                    if (StringUtils.isNotBlank(dto.getName())) {
                        updateReq.setName(SecurityUser.getUser().getUsername() + "_" + dto.getName());
                    }

                    // 2. Support parser configuration (parse string configuration if supplied, though a typed DTO is preferred)
                    if (StringUtils.isNotBlank(dto.getParserConfig())) {
                        try {
                            DatasetDTO.ParserConfig parserConfig = JsonUtils.parseObject(dto.getParserConfig(),
                                    DatasetDTO.ParserConfig.class);
                            updateReq.setParserConfig(parserConfig);
                        } catch (Exception e) {
                            log.warn("Failed to parse parser_config; skipping synchronization", e);
                        }
                    }

                    adapter.updateDataset(entity.getDatasetId(), updateReq);
                    log.info("RAG update succeeded: {}", entity.getDatasetId());
                }
            } catch (Exception e) {
                log.error("RAG update failed", e);
                // Restore transactional consistency: roll back everything if RAG fails
                if (e instanceof RenException) {
                    throw (RenException) e;
                }
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAG update failed: " + e.getMessage());
            }
        }

        BeanUtils.copyProperties(dto, entity);
        knowledgeBaseDao.updateById(entity);

        // Clean cache
        redisUtils.delete(RedisKeys.getKnowledgeBaseCacheKey(entity.getId()));

        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteByDatasetId(String datasetId) {
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>().eq("dataset_id", datasetId));

        // 1. Restore the not-found check: throw if the record does not exist
        if (entity == null) {
            log.warn("Record not found, datasetId: {}", datasetId);
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        log.info("Found record: ID={}, datasetId={}, ragModelId={}",
                entity.getId(), entity.getDatasetId(), entity.getRagModelId());

        // 2. RAG Delete (Strict Mode)
        // Restore strict consistency: throw on RAG deletion failure to roll back; never delete only local data and leave remote data behind
        boolean apiDeleteSuccess = false;
        if (StringUtils.isNotBlank(entity.getRagModelId()) && StringUtils.isNotBlank(entity.getDatasetId())) {
            try {
                KnowledgeBaseAdapter adapter = getAdapterByModelId(entity.getRagModelId());
                if (adapter != null) {
                    adapter.deleteDataset(
                            DatasetDTO.BatchIdReq.builder().ids(Collections.singletonList(datasetId)).build());
                }
                apiDeleteSuccess = true;
            } catch (Exception e) {
                log.error("RAG deletion failed; rolling back", e);
                if (e instanceof RenException) {
                    throw (RenException) e;
                }
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAG deletion failed: " + e.getMessage());
            }
        } else {
            log.warn("datasetId or ragModelId is empty; skipping RAG deletion");
            apiDeleteSuccess = true; // Treat absence of a RAG dataset as success
        }

        // 3. Local Delete (Safe Order)
        // Restore deletion order: delete plugin mapping children before the entity parent
        if (apiDeleteSuccess) {
            log.info("Deleting ai_agent_plugin_mapping records associated with knowledge base ID '{}'", entity.getId());
            log.info("Deleting associated data, entityId: {}", entity.getId());
            knowledgeBaseDao.deletePluginMappingByKnowledgeBaseId(entity.getId());
            log.info("Plugin mappings deleted");
            int deleteCount = knowledgeBaseDao.deleteById(entity.getId());
            log.info("Local database deletion result: {}", deleteCount > 0 ? "Success" : "Failure");
            redisUtils.delete(RedisKeys.getKnowledgeBaseCacheKey(entity.getId()));
        }
    }

    @Override
    public List<KnowledgeBaseDTO> getByDatasetIdList(List<String> datasetIdList) {
        if (datasetIdList == null || datasetIdList.isEmpty()) {
            return Collections.emptyList();
        }
        // [Production Fix] Batch lookup accepting compatible IDs
        QueryWrapper<KnowledgeBaseEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.in("dataset_id", datasetIdList).or().in("id", datasetIdList);
        List<KnowledgeBaseEntity> list = knowledgeBaseDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(list, KnowledgeBaseDTO.class);
    }

    @Override
    public Map<String, Object> getRAGConfig(String ragModelId) {
        return getValidatedRAGConfig(ragModelId);
    }

    @Override
    public Map<String, Object> getRAGConfigByDatasetId(String datasetId) {
        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>().eq("dataset_id", datasetId));
        if (entity == null || StringUtils.isBlank(entity.getRagModelId())) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }
        return getRAGConfig(entity.getRagModelId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateStatistics(String datasetId, Integer docDelta, Long chunkDelta, Long tokenDelta) {
        log.info("Incrementally updating knowledge base statistics: datasetId={}, docs={}, chunks={}, tokens={}", datasetId, docDelta, chunkDelta, tokenDelta);
        knowledgeBaseDao.updateStatsAfterChange(datasetId, docDelta, chunkDelta, tokenDelta);
    }

    @Override
    public List<ModelConfigEntity> getRAGModels() {
        return modelConfigDao.selectList(new QueryWrapper<ModelConfigEntity>()
                .select("id", "model_name", "config_json") // Explicitly select needed fields
                .eq("model_type", Constant.RAG_CONFIG_TYPE)
                .eq("is_enabled", 1)
                .orderByDesc("is_default")
                .orderByDesc("create_date"));
    }

    // --- Helpers ---

    private void checkDuplicateName(String name, String excludeId) {
        if (StringUtils.isBlank(name))
            return;
        QueryWrapper<KnowledgeBaseEntity> qw = new QueryWrapper<>();
        qw.eq("name", name).eq("creator", SecurityUser.getUserId());
        if (excludeId != null)
            qw.ne("id", excludeId);
        if (knowledgeBaseDao.selectCount(qw) > 0) {
            throw new RenException(ErrorCode.KNOWLEDGE_BASE_NAME_EXISTS);
        }
    }

    private KnowledgeBaseAdapter getAdapterByModelId(String modelId) {
        Map<String, Object> config = getValidatedRAGConfig(modelId);
        return KnowledgeBaseAdapterFactory.getAdapter((String) config.get("type"), config);
    }

    private Map<String, Object> getValidatedRAGConfig(String modelId) {
        ModelConfigEntity configEntity = modelConfigService.getModelByIdFromCache(modelId);
        if (configEntity == null || configEntity.getConfigJson() == null) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }
        Map<String, Object> config = new HashMap<>(configEntity.getConfigJson());
        if (!config.containsKey("type")) {
            config.put("type", "ragflow");
        }
        return config;
    }
}
