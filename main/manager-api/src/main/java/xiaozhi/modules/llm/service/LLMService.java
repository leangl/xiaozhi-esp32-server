package xiaozhi.modules.llm.service;

/**
 * LLM service interface
 * Supports calls to multiple large language models
 */
public interface LLMService {

    /**
     * Generate a chat history summary
     * 
     * @param conversation conversation content
     * @param promptTemplate prompt template
     * @return summary
     */
    String generateSummary(String conversation, String promptTemplate);

    /**
     * Generate a chat history summary using the default prompt
     * 
     * @param conversation conversation content
     * @return summary
     */
    String generateSummary(String conversation);

    /**
     * Generate a chat history summary using a specified model ID
     * 
     * @param conversation conversation content
     * @param modelId model ID
     * @return summary
     */
    String generateSummaryWithModel(String conversation, String modelId);

    /**
     * Generate a chat history summary using a specified model ID and prompt template
     * 
     * @param conversation conversation content
     * @param promptTemplate prompt template
     * @param modelId model ID
     * @return summary
     */
    String generateSummary(String conversation, String promptTemplate, String modelId);

    /**
     * Generate a chat summary, merging existing memory
     * 
     * @param conversation conversation content
     * @param historyMemory existing memory
     * @param promptTemplate prompt template
     * @param modelId model ID
     * @return summary
     */
    String generateSummaryWithHistory(String conversation, String historyMemory, String promptTemplate, String modelId);

    /**
     * Check service availability
     * 
     * @return whether available
     */
    boolean isAvailable();

    /**
     * Check availability of a specified model
     * 
     * @param modelId model ID
     * @return whether available
     */
    boolean isAvailable(String modelId);

    /**
     * Generate a session title
     * 
     * @param conversation conversation content
     * @param modelId model ID
     * @return title of approximately 15 characters
     */
    String generateTitle(String conversation, String modelId);
}
