package xiaozhi.modules.knowledge.rag.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.stream.Stream;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.MockedStatic;
import org.slf4j.LoggerFactory;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;
import xiaozhi.modules.knowledge.rag.RAGFlowClient;

class RAGFlowAdapterFailureLoggingTest {
    private static final String PRIVATE = "https://unknown.example/private?api_key=synthetic-secret raw-response-body";
    private RAGFlowAdapter adapter;
    private RAGFlowClient client;
    private ListAppender<ILoggingEvent> logs;
    private Logger logger;
    private MockedStatic<MessageUtils> messages;

    @BeforeEach void setup() {
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt(), any(String[].class)))
                .thenAnswer(invocation -> "RAG error: " + invocation.getArgument(1));
        adapter = new RAGFlowAdapter();
        client = mock(RAGFlowClient.class);
        ReflectionTestUtils.setField(adapter, "client", client);
        ReflectionTestUtils.setField(adapter, "config", Map.of());
        logs = new ListAppender<>();
        logs.start();
        logger = (Logger) LoggerFactory.getLogger(RAGFlowAdapter.class);
        logger.addAppender(logs);
    }

    @AfterEach void cleanup() {
        logger.detachAppender(logs);
        logs.stop();
        messages.close();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("failingOperations")
    void transportFailuresAreNotLoggedButTheExistingExceptionIsPreserved(String name, Consumer<RAGFlowAdapter> operation) {
        var original = new RenException(PRIVATE);
        when(client.get(anyString(), any())).thenThrow(original);
        when(client.post(anyString(), any())).thenThrow(original);
        when(client.put(anyString(), any())).thenThrow(original);
        when(client.delete(anyString(), any())).thenThrow(original);
        when(client.postMultipart(anyString(), any())).thenThrow(original);
        doThrow(original).when(client).postStream(anyString(), any(), any());
        assertSame(original, assertThrows(RenException.class, () -> operation.accept(adapter)));
        assertPrivateDataWasNotLogged();
    }

    static Stream<Arguments> failingOperations() {
        return Stream.of(
                Arguments.of("getDocumentList", (Consumer<RAGFlowAdapter>) a -> a.getDocumentList(PRIVATE, DocumentDTO.ListReq.builder().build())),
                Arguments.of("getDocumentById", (Consumer<RAGFlowAdapter>) a -> a.getDocumentById(PRIVATE, PRIVATE)),
                Arguments.of("uploadDocument", (Consumer<RAGFlowAdapter>) a -> a.uploadDocument(DocumentDTO.UploadReq.builder()
                        .datasetId(PRIVATE).file(new MockMultipartFile("file", "synthetic.txt", "text/plain", new byte[]{1})).build())),
                Arguments.of("deleteDocument", (Consumer<RAGFlowAdapter>) a -> a.deleteDocument(PRIVATE, DocumentDTO.BatchIdReq.builder().ids(List.of(PRIVATE)).build())),
                Arguments.of("parseDocuments", (Consumer<RAGFlowAdapter>) a -> a.parseDocuments(PRIVATE, List.of(PRIVATE))),
                Arguments.of("listChunks", (Consumer<RAGFlowAdapter>) a -> a.listChunks(PRIVATE, PRIVATE, ChunkDTO.ListReq.builder().build())),
                Arguments.of("retrievalTest", (Consumer<RAGFlowAdapter>) a -> a.retrievalTest(RetrievalDTO.TestReq.builder().build())),
                Arguments.of("createDataset", (Consumer<RAGFlowAdapter>) a -> a.createDataset(DatasetDTO.CreateReq.builder().build())),
                Arguments.of("updateDataset", (Consumer<RAGFlowAdapter>) a -> a.updateDataset(PRIVATE, DatasetDTO.UpdateReq.builder().build())),
                Arguments.of("deleteDataset", (Consumer<RAGFlowAdapter>) a -> a.deleteDataset(DatasetDTO.BatchIdReq.builder().ids(List.of(PRIVATE)).build())),
                Arguments.of("getDatasetInfo", (Consumer<RAGFlowAdapter>) a -> a.getDatasetInfo(PRIVATE)),
                Arguments.of("postStream", (Consumer<RAGFlowAdapter>) a -> a.postStream(PRIVATE, Map.of(), ignored -> {})),
                Arguments.of("postSearchBotAsk", (Consumer<RAGFlowAdapter>) a -> a.postSearchBotAsk(Map.of(), Map.of(), ignored -> {})),
                Arguments.of("postAgentBotCompletion", (Consumer<RAGFlowAdapter>) a -> a.postAgentBotCompletion(Map.of(), PRIVATE, Map.of(), ignored -> {})));
    }

    @Test
    void connectionFailureStillReturnsFalseWithoutLoggingItsMessageOrCause() {
        when(client.get(anyString(), any())).thenThrow(new IllegalArgumentException(PRIVATE));
        assertFalse(adapter.testConnection());
        assertPrivateDataWasNotLogged();
    }

    @Test
    void rejectedStoredConfigurationStillReturnsUnavailableStatusWithoutLeakingIt() {
        ReflectionTestUtils.setField(adapter, "client", null);
        ReflectionTestUtils.setField(adapter, "config", Map.of("base_url", PRIVATE, "api_key", "synthetic-secret"));
        Map<String, Object> status = adapter.getStatus();
        assertEquals("ragflow", status.get("adapterType"));
        assertEquals(false, status.get("connectionTest"));
        assertTrue(status.containsKey("lastChecked"));
        assertPrivateDataWasNotLogged();
    }

    @Test
    void malformedDocumentIsSkippedWithoutChangingValidRecordsOrTotal() {
        when(client.get(anyString(), any())).thenReturn(Map.of("data", Map.of("docs", List.of(
                Map.of("id", "good-id", "name", "synthetic.txt", "size", 7, "status", "1"),
                Map.of("id", "bad-id", "size", PRIVATE)), "total", 2)));
        var page = adapter.getDocumentList("synthetic-dataset", DocumentDTO.ListReq.builder().build());
        assertEquals(2, page.getTotal());
        assertEquals(1, page.getList().size());
        assertEquals("good-id", page.getList().getFirst().getId());
        assertEquals("synthetic.txt", page.getList().getFirst().getName());
        assertPrivateDataWasNotLogged();
    }

    @Test
    void malformedUploadResponseKeepsTheExistingFallbackDtoWithoutLoggingTheBody() {
        when(client.postMultipart(anyString(), any())).thenReturn(Map.of("data", Map.of("size", PRIVATE)));
        var file = new MockMultipartFile("file", "synthetic.txt", "text/plain", new byte[]{1, 2, 3});
        var result = adapter.uploadDocument(DocumentDTO.UploadReq.builder().datasetId("synthetic-dataset").file(file).build());
        assertEquals("synthetic-dataset", result.getDatasetId());
        assertEquals("synthetic.txt", result.getName());
        assertEquals(3L, result.getFileSize());
        assertEquals("1", result.getStatus());
        assertNull(result.getId());
        assertPrivateDataWasNotLogged();
    }

    @Test
    void conversionFailureRetainsTheExistingRagErrorEnvelopeWithoutLoggingPayload() {
        when(client.get(anyString(), any())).thenReturn(Map.of("data", List.of(Map.of("document_count", PRIVATE))));
        var error = assertThrows(RenException.class, () -> adapter.getDatasetInfo("synthetic-dataset"));
        assertEquals(ErrorCode.RAG_API_ERROR, error.getCode());
        assertNull(error.getCause());
        assertPrivateDataWasNotLogged();
    }

    @Test
    void validUploadResultRemainsUnchanged() {
        when(client.postMultipart(anyString(), any())).thenReturn(Map.of("data", Map.of(
                "id", "synthetic-document", "name", "synthetic.txt", "size", 3, "progress_msg", "synthetic-progress")));
        var result = adapter.uploadDocument(DocumentDTO.UploadReq.builder().datasetId("synthetic-dataset")
                .file(new MockMultipartFile("file", "synthetic.txt", "text/plain", new byte[]{1, 2, 3})).build());
        assertEquals("synthetic-document", result.getId());
        assertEquals("synthetic-document", result.getDocumentId());
        assertEquals("synthetic-progress", result.getError());
    }

    private void assertPrivateDataWasNotLogged() {
        assertFalse(logs.list.isEmpty());
        for (var event : logs.list) {
            String message = event.getFormattedMessage();
            assertFalse(message.contains("unknown.example"), "URL must not be logged");
            assertFalse(message.contains("synthetic-secret"), "Credential must not be logged");
            assertFalse(message.contains("raw-response-body"), "Payload must not be logged");
            assertNull(event.getThrowableProxy(), "Exception chains can contain response bodies and credentials");
        }
    }
}
