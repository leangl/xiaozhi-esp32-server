package xiaozhi.modules.agent.service;

import java.util.List;
import java.util.Map;

import com.baomidou.mybatisplus.extension.repository.IRepository;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.agent.dto.AgentChatHistoryDTO;
import xiaozhi.modules.agent.dto.AgentChatSessionDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.vo.AgentChatHistoryUserVO;

/**
 * Agent chat history service
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentChatHistoryService extends IRepository<AgentChatHistoryEntity> {

    /**
     * Get sessions by agent ID
     *
     * @param params query parameters including agentId, page, and limit
     * @return paginated session list
     */
    PageData<AgentChatSessionDTO> getSessionListByAgentId(Map<String, Object> params);

    /**
     * Get chat records by session ID
     *
     * @param agentId agent ID
     * @param sessionId session ID
     * @return chat record list
     */
    List<AgentChatHistoryDTO> getChatHistoryBySessionId(String agentId, String sessionId);

    /**
     * Get agent ID by session ID
     *
     * @param sessionId session ID
     * @return agent ID
     */
    String getAgentIdBySessionId(String sessionId);

    /**
     * Delete chat history by agent ID
     *
     * @param agentId agent ID
     * @param deleteAudio whether to delete audio
     * @param deleteText whether to delete text
     */
    void deleteByAgentId(String agentId, Boolean deleteAudio, Boolean deleteText);

    /**
     * Get the latest 50 user chat records with audio by agent ID
     *
     * @param agentId agent ID
     * @return chat records (user messages only)
     */
    List<AgentChatHistoryUserVO> getRecentlyFiftyByAgentId(String agentId);

    /**
     * Get chat content by audio data ID
     *
     * @param audioId audio ID
     * @return chat content
     */
    String getContentByAudioId(String audioId);

    /**
     * Get agent ID by audio ID
     *
     * @param audioId audio ID
     * @return agent ID
     */
    String getAgentIdByAudioId(String audioId);


    /**
     * Check whether an audio ID belongs to the agent
     *
     * @param audioId audio ID
     * @param agentId audio ID
     * @return true if it belongs to the agent, false otherwise
     */
    boolean isAudioOwnedByAgent(String audioId,String agentId);
}
