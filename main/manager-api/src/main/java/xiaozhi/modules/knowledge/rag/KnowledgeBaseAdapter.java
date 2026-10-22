package xiaozhi.modules.knowledge.rag;

import java.util.List;
import java.util.Map;

import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import java.util.function.Consumer;

/**
 * Abstract knowledge base API adapter
 * Defines common knowledge base operations for multiple backend API implementations
 */
public abstract class KnowledgeBaseAdapter {

        /**
         * Get the adapter type identifier
         * 
         * @return adapter type, such as ragflow, milvus, or pinecone
         */
        public abstract String getAdapterType();

        /**
         * Initialize adapter configuration
         * 
         * @param config configuration parameters
         */
        public abstract void initialize(Map<String, Object> config);

        /**
         * Validate configuration
         * 
         * @param config configuration parameters
         * @return validation result
         */
        public abstract boolean validateConfig(Map<String, Object> config);

        /**
         * Query paginated documents
         * 
         * @param datasetId knowledge base ID
         * @param queryParams query parameters
         * @param page page number
         * @param limit records per page
         * @return paginated data
         */
        public abstract PageData<KnowledgeFilesDTO> getDocumentList(String datasetId,
                        DocumentDTO.ListReq req);

        /**
         * Get document details by document ID
         * 
         * @param datasetId knowledge base ID
         * @param documentId document ID
         * @return document details (strongly typed InfoVO)
         */
        public abstract DocumentDTO.InfoVO getDocumentById(String datasetId, String documentId);

        /**
         * Upload a document to a knowledge base
         * 
         * @param req upload request parameters
         * @return uploaded document information
         */
        public abstract KnowledgeFilesDTO uploadDocument(DocumentDTO.UploadReq req);

        /**
         * Query paginated documents by status
         * 
         * @param datasetId knowledge base ID
         * @param status document parsing status
         * @param page page number
         * @param limit records per page
         * @return paginated data
         */
        public abstract PageData<KnowledgeFilesDTO> getDocumentListByStatus(String datasetId,
                        Integer status,
                        Integer page,
                        Integer limit);

        /**
         * Delete documents, supporting batch deletion
         * 
         * @param datasetId knowledge base ID
         * @param req request containing document IDs
         */
        public abstract void deleteDocument(String datasetId, DocumentDTO.BatchIdReq req);

        /**
         * Parse documents into chunks
         * 
         * @param datasetId knowledge base ID
         * @param documentIds document ID list
         * @return parsing result
         */
        public abstract boolean parseDocuments(String datasetId, List<String> documentIds);

        /**
         * List chunks for a document
         * 
         * @param datasetId knowledge base ID
         * @param documentId document ID
         * @param req list request parameters (pagination, keyword, etc.)
         * @return chunk list VO
         */
        public abstract ChunkDTO.ListVO listChunks(String datasetId,
                        String documentId,
                        ChunkDTO.ListReq req);

        /**
         * Recall test: retrieve relevant knowledge base chunks
         * 
         * @param req retrieval test request parameters
         * @return recall test result
         */
        public abstract RetrievalDTO.ResultVO retrievalTest(
                        RetrievalDTO.TestReq req);

        /**
         * Test the connection
         * 
         * @return connection test result
         */
        public abstract boolean testConnection();

        /**
         * Get adapter status information
         * 
         * @return status information
         */
        public abstract Map<String, Object> getStatus();

        /**
         * Get supported configuration parameters
         * 
         * @return configuration parameter descriptions
         */
        public abstract Map<String, Object> getSupportedConfig();

        /**
         * Get the default configuration
         * 
         * @return default configuration
         */
        public abstract Map<String, Object> getDefaultConfig();

        /**
         * Create a dataset
         * 
         * @param req creation parameters
         * @return dataset details
         */
        public abstract DatasetDTO.InfoVO createDataset(DatasetDTO.CreateReq req);

        /**
         * Update a dataset
         * 
         * @param datasetId dataset ID
         * @param req update parameters
         * @return dataset details
         */
        public abstract DatasetDTO.InfoVO updateDataset(String datasetId, DatasetDTO.UpdateReq req);

        /**
         * Delete datasets
         * 
         * @param req deletion request containing IDs
         * @return batch operation result
         */
        public abstract DatasetDTO.BatchOperationVO deleteDataset(DatasetDTO.BatchIdReq req);

        /**
         * Get the dataset document count
         *
         * @param datasetId dataset ID
         * @return document count
         */
        public abstract Integer getDocumentCount(String datasetId);

        /**
         * Get complete dataset information, including name, description, and document count
         * Detect remote RAGFlow deletion and synchronize name/description changes
         *
         * @param datasetId dataset ID
         * @return dataset details, or null if absent from RAGFlow
         */
        public abstract DatasetDTO.InfoVO getDatasetInfo(String datasetId);

        /**
         * Send a streaming request (SSE)
         * 
         * @param endpoint API endpoint
         * @param body request body
         * @param onData data callback
         */
        public abstract void postStream(String endpoint, Object body, Consumer<String> onData);

        /**
         * SearchBot question
         *
         * @param config RAG configuration
         * @param body request body
         * @param onData data callback
         * @return response object
         */
        public abstract Object postSearchBotAsk(Map<String, Object> config, Object body,
                        Consumer<String> onData);

        /**
         * AgentBot conversation
         *
         * @param config RAG configuration
         * @param agentId Agent ID
         * @param body request body
         * @param onData data callback
         */
        public abstract void postAgentBotCompletion(Map<String, Object> config, String agentId, Object body,
                        Consumer<String> onData);
}
