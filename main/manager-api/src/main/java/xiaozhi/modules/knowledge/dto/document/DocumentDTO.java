package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Document management aggregate DTO
 */
@Schema(description = "Document management aggregate DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class DocumentDTO {

    /**
     * Upload document request parameters
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Upload document request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UploadReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Knowledge base ID (ownership required)", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        @NotBlank(message = "Knowledge base ID must not be empty")
        private String datasetId;

        @Schema(description = "File name, overriding the original if specified")
        private String name;

        @Schema(description = "Chunking method")
        @JsonProperty("chunk_method")
        private DocumentDTO.InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "Parser parameter configuration")
        @JsonProperty("parser_config")
        private DocumentDTO.InfoVO.ParserConfig parserConfig;

        @Schema(description = "Virtual folder path (default: /)")
        @JsonProperty("parent_path")
        private String parentPath;

        @Schema(description = "Metadata fields")
        @JsonProperty("meta")
        private Map<String, Object> metaFields;

        @Schema(description = "Binary file stream (supports PDF, DOCX, TXT, MD, and other formats)", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull(message = "Uploaded file must not be empty")
        private org.springframework.web.multipart.MultipartFile file;
    }

    /**
     * Update document request parameters
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Update document request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "New document name (must include extension and preserve the original type)")
        private String name;

        @Schema(description = "Enable/disable (true: enabled, false: disabled; disabled documents are excluded from retrieval)")
        private Boolean enabled;

        @Schema(description = "New parsing method (resets parsing status when changed)")
        @JsonProperty("chunk_method")
        private InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "New parser details (use with chunk_method)")
        @JsonProperty("parser_config")
        private InfoVO.ParserConfig parserConfig;
    }

    /**
     * List documents request parameters
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "List documents request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Page number (default: 1)")
        private Integer page;

        @Schema(description = "Records per page (default: 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Sort field (create_time, name, or size; default: create_time)")
        private String orderby;

        @Schema(description = "Descending order (true: newest/largest first; false: oldest/smallest first; default: true)")
        private Boolean desc;

        @Schema(description = "Exact filter: document ID")
        private String id;

        @Schema(description = "Exact filter: full document name including extension")
        private String name;

        @Schema(description = "Fuzzy search: document name keywords")
        private String keywords;

        @Schema(description = "Filter: file extensions, such as ['pdf', 'docx']")
        private List<String> suffix;

        @Schema(description = "Filter: run statuses")
        private List<InfoVO.RunStatus> run;

        @Schema(description = "Filter: creation time lower bound (Unix milliseconds)")
        @JsonProperty("create_time_from")
        private Long createTimeFrom;

        @Schema(description = "Filter: creation time upper bound (Unix milliseconds)")
        @JsonProperty("create_time_to")
        private Long createTimeTo;
    }

    /**
     * Batch document operation parameters (deletion, parsing, etc.)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Batch document operation request parameters")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BatchIdReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID list", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("ids") // document_ids could be supported for compatibility, but this API consistently uses ids
        @JsonAlias("document_ids")
        @NotEmpty(message = "Document ID list must not be empty")
        private List<String> ids;
    }

    /**
     * Knowledge base document information VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Knowledge base document information")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID (unique identifier)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Document thumbnail (Base64 or URL)")
        private String thumbnail;

        @Schema(description = "Owner knowledge base ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Document parsing method, determining chunking")
        @JsonProperty("chunk_method")
        private ChunkMethod chunkMethod;

        @Schema(description = "Associated ETL Pipeline ID, if any")
        @JsonProperty("pipeline_id")
        private String pipelineId;

        @Schema(description = "Detailed document parser configuration")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;

        @Schema(description = "Source type, such as local, s3, or url")
        @JsonProperty("source_type")
        private String sourceType;

        @Schema(description = "Document file type, such as pdf, docx, or txt", requiredMode = Schema.RequiredMode.REQUIRED)
        private String type;

        @Schema(description = "Creator user ID")
        @JsonProperty("created_by")
        private String createdBy;

        @Schema(description = "Document name including extension", requiredMode = Schema.RequiredMode.REQUIRED)
        private String name;

        @Schema(description = "File storage path or location identifier")
        private String location;

        @Schema(description = "File size in bytes")
        private Long size;

        @Schema(description = "Total tokens, counted after parsing")
        @JsonProperty("token_count")
        private Long tokenCount;

        @Schema(description = "Total chunks")
        @JsonProperty("chunk_count")
        private Long chunkCount;

        @Schema(description = "Parsing progress (0.0 ~ 1.0; 1.0 means complete)")
        private Double progress;

        @Schema(description = "Current progress description or error message")
        @JsonProperty("progress_msg")
        private String progressMsg;

        @Schema(description = "Processing start timestamp (RFC1123 from RAGFlow)")
        @JsonProperty("process_begin_at")
        private String processBeginAt;

        @Schema(description = "Total processing duration in seconds")
        @JsonProperty("process_duration")
        private Double processDuration;

        @Schema(description = "Custom metadata fields (key-value pairs)")
        @JsonProperty("meta_fields")
        private Map<String, Object> metaFields;

        @Schema(description = "File extension without the dot")
        private String suffix;

        @Schema(description = "Document parsing run status")
        private RunStatus run;

        @Schema(description = "Document availability (1: enabled/normal, 0: disabled/invalid)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String status;

        @Schema(description = "Creation timestamp in milliseconds", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Creation date (RFC1123 from RAGFlow)")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Last update timestamp in milliseconds")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Last update date (RFC1123 from RAGFlow)")
        @JsonProperty("update_date")
        private String updateDate;

        /**
         * Parsing method enumeration (ChunkMethod)
         */
        public enum ChunkMethod {
            @Schema(description = "General mode: suitable for most plain-text or mixed documents")
            @JsonProperty("naive")
            NAIVE,
            @Schema(description = "Manual mode: allows manual chunk editing")
            @JsonProperty("manual")
            MANUAL,
            @Schema(description = "Q&A mode: optimized for question-and-answer documents")
            @JsonProperty("qa")
            QA,
            @Schema(description = "Table mode: optimized for spreadsheet data such as Excel or CSV")
            @JsonProperty("table")
            TABLE,
            @Schema(description = "Paper mode: optimized for academic paper layouts")
            @JsonProperty("paper")
            PAPER,
            @Schema(description = "Book mode: optimized for book chapter structure")
            @JsonProperty("book")
            BOOK,
            @Schema(description = "Legal mode: optimized for statutory text structure")
            @JsonProperty("laws")
            LAWS,
            @Schema(description = "Presentation mode: optimized for slides such as PPT")
            @JsonProperty("presentation")
            PRESENTATION,
            @Schema(description = "Image mode: applies OCR and descriptions to images")
            @JsonProperty("picture")
            PICTURE,
            @Schema(description = "Whole-document mode: treats the entire document as one chunk")
            @JsonProperty("one")
            ONE,
            @Schema(description = "Knowledge graph mode: extracts entity relationships to build a graph")
            @JsonProperty("knowledge_graph")
            KNOWLEDGE_GRAPH,
            @Schema(description = "Email mode: optimized for email formats")
            @JsonProperty("email")
            EMAIL;
        }

        /**
         * Run status enumeration (RunStatus)
         */
        public enum RunStatus {
            @Schema(description = "Not started: waiting in the parsing queue")
            @JsonProperty("UNSTART")
            UNSTART,
            @Schema(description = "Running: parsing or indexing")
            @JsonProperty("RUNNING")
            RUNNING,
            @Schema(description = "Canceled: manually canceled by the user")
            @JsonProperty("CANCEL")
            CANCEL,
            @Schema(description = "Completed: parsing succeeded")
            @JsonProperty("DONE")
            DONE,
            @Schema(description = "Failed: error during parsing")
            @JsonProperty("FAIL")
            FAIL;
        }

        /**
         * Layout recognition model enumeration
         */
        public enum LayoutRecognize {
            @Schema(description = "Deep document understanding model: suitable for complex layouts")
            @JsonProperty("DeepDOC")
            DeepDOC,
            @Schema(description = "Simple rule-based model: suitable for plain text")
            @JsonProperty("Simple")
            Simple;
        }

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Document parser parameters")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class ParserConfig implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Maximum tokens per chunk (suggested: 512, 1024, 2048)")
            @JsonProperty("chunk_token_num")
            private Integer chunkTokenNum;

            @Schema(description = "Paragraph delimiter (supports escapes such as \\n)")
            private String delimiter;

            @Schema(description = "Layout recognition model (DeepDOC/Simple)")
            @JsonProperty("layout_recognize")
            private LayoutRecognize layoutRecognize;

            @Schema(description = "Whether to convert Excel to HTML tables")
            @JsonProperty("html4excel")
            private Boolean html4excel;

            @Schema(description = "Automatically extracted keyword count (0: disabled)")
            @JsonProperty("auto_keywords")
            private Integer autoKeywords;

            @Schema(description = "Automatically generated question count (0: disabled)")
            @JsonProperty("auto_questions")
            private Integer autoQuestions;

            @Schema(description = "Automatically generated tag count")
            @JsonProperty("topn_tags")
            private Integer topnTags;

            @Schema(description = "RAPTOR advanced indexing configuration")
            private RaptorConfig raptor;

            @Schema(description = "GraphRAG knowledge graph configuration")
            @JsonProperty("graphrag")
            private GraphRagConfig graphRag;

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "RAPTOR recursive summary indexing configuration")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class RaptorConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether RAPTOR indexing is enabled")
                @JsonProperty("use_raptor")
                private Boolean useRaptor;
            }

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "GraphRAG graph-enhanced retrieval configuration")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class GraphRagConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether GraphRAG indexing is enabled")
                @JsonProperty("use_graphrag")
                private Boolean useGraphRag;
            }
        }
    }
}
