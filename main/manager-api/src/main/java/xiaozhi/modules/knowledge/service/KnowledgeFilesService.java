package xiaozhi.modules.knowledge.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;

/**
 * Knowledge base document service interface
 */
public interface KnowledgeFilesService {

        /**
         * Query paginated documents
         * 
         * @param knowledgeFilesDTO query filters
         * @param page page number
         * @param limit records per page
         * @return paginated data
         */
        PageData<KnowledgeFilesDTO> getPageList(KnowledgeFilesDTO knowledgeFilesDTO, Integer page, Integer limit);

        /**
         * Get document details by document ID and knowledge base ID
         * 
         * @param documentId document ID
         * @param datasetId knowledge base ID
         * @return document details (strongly typed InfoVO)
         */
        DocumentDTO.InfoVO getByDocumentId(String documentId, String datasetId);

        /**
         * Upload a document to a knowledge base
         * 
         * @param datasetId knowledge base ID
         * @param file uploaded file
         * @param name document name
         * @param metaFields metadata fields
         * @param chunkMethod chunking method
         * @param parserConfig parser configuration
         * @return uploaded document information
         */
        KnowledgeFilesDTO uploadDocument(String datasetId, MultipartFile file, String name,
                        Map<String, Object> metaFields, String chunkMethod,
                        Map<String, Object> parserConfig);

        /**
         * Batch delete documents
         * 
         * @param datasetId knowledge base ID
         * @param req deletion request containing document IDs
         */
        void deleteDocuments(String datasetId, DocumentDTO.BatchIdReq req);

        /**
         * Get RAG configuration information
         * 
         * @param ragModelId RAG model configuration ID
         * @return RAG configuration information
         */
        Map<String, Object> getRAGConfig(String ragModelId);

        /**
         * Parse documents into chunks
         * 
         * @param datasetId knowledge base ID
         * @param documentIds document ID list
         * @return parsing result
         */
        boolean parseDocuments(String datasetId, List<String> documentIds);

        /**
         * List chunks for a document
         * 
         * @param datasetId knowledge base ID
         * @param documentId document ID
         * @param req chunk list request parameters
         * @return chunk list information
         */
        ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req);

        /**
         * Recall test
         * 
         * @param req retrieval test request parameters
         * @return recall test result
         */
        RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req);

        /**
         * Save a shadow document record
         */
        boolean saveDocumentShadow(String datasetId, KnowledgeFilesDTO result, String originalName, String chunkMethod,
                        Map<String, Object> parserConfig);

        /**
         * Batch delete shadow document records and update statistics
         * 
         * @param documentIds document ID list
         * @param datasetId dataset ID
         * @param chunkDelta total chunk count to subtract
         * @param tokenDelta total token count to subtract
         */
        void deleteDocumentShadows(List<String> documentIds, String datasetId, Long chunkDelta, Long tokenDelta);

        /**
         * Delete all associated documents by dataset ID, for cascading deletion
         * 
         * @param datasetId dataset ID
         */
        void deleteDocumentsByDatasetId(String datasetId);

        /**
         * Synchronize all RUNNING documents, called by scheduled tasks
         */
        void syncRunningDocuments();

        /**
         * Fully synchronize RAGFlow documents to the local shadow table
         * Fetch all remote documents, compare with the shadow table, and insert missing records
         *
         * @param datasetId dataset ID
         * @return newly synchronized document count
         */
        int syncDocumentsFromRAG(String datasetId);
}
