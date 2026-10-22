package xiaozhi.modules.knowledge.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;

/**
 * Scheduled knowledge base document status synchronization
 * 
 * Purpose:
 * 1. Scan documents in RUNNING (parsing) state
 * 2. Call RAGFlow for the latest status
 * 3. Update the database on RUNNING -> SUCCESS/FAIL transitions
 * 4. [Important] Compensate knowledge base statistics (TokenCount) after successful parsing
 */
@Component
@AllArgsConstructor
@Slf4j
public class DocumentStatusSyncTask {

    private final KnowledgeFilesService knowledgeFilesService;

    /**
     * Synchronize every 30 seconds
     * Use fixedDelay to wait 30 seconds after the previous run finishes, avoiding backlog
     */
    @Scheduled(fixedDelay = 30000)
    public void syncRunningDocuments() {
        try {
            // log.debug("Starting document status synchronization...");
            knowledgeFilesService.syncRunningDocuments();
        } catch (Exception e) {
            log.error("Document status synchronization task failed", e);
        }
    }
}
