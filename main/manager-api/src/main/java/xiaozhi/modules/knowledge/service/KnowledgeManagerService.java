package xiaozhi.modules.knowledge.service;

import java.util.List;

/**
 * Knowledge base domain orchestration service
 * Coordinates complex workflows across KnowledgeBase and KnowledgeFiles to eliminate circular service dependencies.
 */
public interface KnowledgeManagerService {

    /**
     * Cascade delete a knowledge base and all documents, including local DB and remote RAGFlow data
     * 
     * @param datasetId knowledge base ID
     */
    void deleteDatasetWithFiles(String datasetId);

    /**
     * Batch cascade delete knowledge bases
     * 
     * @param datasetIds knowledge base IDs
     */
    void batchDeleteDatasetsWithFiles(List<String> datasetIds);
}
