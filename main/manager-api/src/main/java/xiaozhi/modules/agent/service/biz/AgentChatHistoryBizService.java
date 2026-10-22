package xiaozhi.modules.agent.service.biz;

import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;

/**
 * Agent chat history business logic
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentChatHistoryBizService {

    /**
     * Chat reporting method
     *
     * @param agentChatHistoryReportDTO input containing the chat report information
     *                                  For example: device MAC address, file type, and content
     * @return upload result: true on success, false on failure
     */
    Boolean report(AgentChatHistoryReportDTO agentChatHistoryReportDTO);
}
