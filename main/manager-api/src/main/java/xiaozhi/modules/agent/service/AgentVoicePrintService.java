package xiaozhi.modules.agent.service;

import java.util.List;

import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.AgentVoicePrintUpdateDTO;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;

/**
 * Agent voiceprint service
 *
 * @author zjy
 */
public interface AgentVoicePrintService {
    /**
     * Add a new voiceprint to an agent
     *
     * @param dto voiceprint data to save
     * @return true on success, false on failure
     */
    boolean insert(AgentVoicePrintSaveDTO dto);

    /**
     * Delete a specified agent voiceprint
     *
     * @param userId logged-in user ID
     * @param voicePrintId voiceprint ID
     * @return true on success, false on failure
     */
    boolean delete(Long userId, String voicePrintId);

    /**
     * Get all voiceprints for an agent
     *
     * @param userId logged-in user ID
     * @param agentId agent ID
     * @return voiceprint data collection
     */
    List<AgentVoicePrintVO> list(Long userId, String agentId);

    /**
     * Update a specified agent voiceprint
     *
     * @param userId logged-in user ID
     * @param dto updated voiceprint data
     * @return true on success, false on failure
     */
    boolean update(Long userId, AgentVoicePrintUpdateDTO dto);

}
