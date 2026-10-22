package xiaozhi.modules.knowledge.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.model.entity.ModelConfigEntity;

/**
 * Knowledge base service interface
 */
public interface KnowledgeBaseService extends BaseService<KnowledgeBaseEntity> {

    /**
     * Query paginated knowledge bases
     * 
     * @param knowledgeBaseDTO query filters
     * @param page page number
     * @param limit records per page
     * @return paginated data
     */
    PageData<KnowledgeBaseDTO> getPageList(KnowledgeBaseDTO knowledgeBaseDTO, Integer page, Integer limit);

    /**
     * Get knowledge base details by ID
     * 
     * @param id knowledge base ID
     * @return knowledge base details
     */
    KnowledgeBaseDTO getById(String id);

    /**
     * Create a knowledge base
     * 
     * @param knowledgeBaseDTO knowledge base information
     * @return created knowledge base
     */
    KnowledgeBaseDTO save(KnowledgeBaseDTO knowledgeBaseDTO);

    /**
     * Update a knowledge base
     * 
     * @param knowledgeBaseDTO knowledge base information
     * @return updated knowledge base
     */
    KnowledgeBaseDTO update(KnowledgeBaseDTO knowledgeBaseDTO);

    /**
     * Query a knowledge base by dataset ID
     * 
     * @param datasetId knowledge base ID
     * @return knowledge base details
     */
    KnowledgeBaseDTO getByDatasetId(String datasetId);

    /**
     * Query knowledge bases by dataset IDs
     *
     * @param datasetIdList knowledge base ID collection
     * @return knowledge base details
     */
    List<KnowledgeBaseDTO> getByDatasetIdList(List<String> datasetIdList);

    /**
     * Delete a knowledge base by dataset ID
     * 
     * @param datasetId knowledge base ID
     */
    void deleteByDatasetId(String datasetId);

    /**
     * Get RAG configuration information
     * 
     * @param ragModelId RAG model configuration ID
     * @return RAG configuration information
     */
    Map<String, Object> getRAGConfig(String ragModelId);

    /**
     * Get the RAG configuration for a knowledge base ID
     * 
     * @param datasetId knowledge base ID
     * @return RAG configuration
     */
    Map<String, Object> getRAGConfigByDatasetId(String datasetId);

    /**
     * Get RAG models
     * 
     * @return RAG model list
     */
    List<ModelConfigEntity> getRAGModels();

    /**
     * Update knowledge base statistics, called back by the file service
     * 
     * @param datasetId knowledge base ID
     * @param docDelta document count delta
     * @param chunkDelta chunk count delta
     * @param tokenDelta token count delta
     */
    void updateStatistics(String datasetId, Integer docDelta, Long chunkDelta, Long tokenDelta);
}
