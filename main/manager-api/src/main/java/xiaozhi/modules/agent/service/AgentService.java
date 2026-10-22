package xiaozhi.modules.agent.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.agent.dto.AgentCreateDTO;
import xiaozhi.modules.agent.dto.AgentDTO;
import xiaozhi.modules.agent.dto.AgentMemoryDTO;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.vo.AgentInfoVO;

/**
 * Agent service
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentService extends BaseService<AgentEntity> {
    /**
     * Get the administrator's agent list
     *
     * @param params query parameters
     * @return paginated data
     */
    PageData<AgentEntity> adminAgentList(Map<String, Object> params);

    /**
     * Get an agent by ID
     *
     * @param id agent ID
     * @return agent entity
     */
    AgentInfoVO getAgentById(String id);

    /**
     * Get an agent accessible to the current user by ID
     *
     * @param id agent ID
     * @param userId current user ID
     * @return agent entity
     */
    AgentInfoVO getAgentById(String id, Long userId);

    /**
     * Insert an agent
     *
     * @param entity agent entity
     * @return whether the operation succeeded
     */
    boolean insert(AgentEntity entity);

    /**
     * Delete agents by user ID
     *
     * @param userId user ID
     */
    void deleteAgentByUserId(Long userId);

    /**
     * Delete an agent and associated data
     *
     * @param agentId agent ID
     */
    void deleteAgent(String agentId);

    /**
     * Get a user's agents
     *
     * @param userId user ID
     * @param keyword search keyword
     * @param searchType search type (name: search by name, mac: search by MAC address)
     * @return agent list
     */
    List<AgentDTO> getUserAgents(Long userId, String keyword, String searchType);

    /**
     * Get device count by agent ID
     *
     * @param agentId agent ID
     * @return device count
     */
    Integer getDeviceCountByAgentId(String agentId);

    /**
     * Look up the default agent for a device MAC address
     *
     * @param macAddress device MAC address
     * @return default agent information, or null if absent
     */
    AgentEntity getDefaultAgentByMacAddress(String macAddress);

    /**
     * Check whether a user may access an agent
     *
     * @param agentId agent ID
     * @param userId user ID
     * @return whether access is allowed
     */
    boolean checkAgentPermission(String agentId, Long userId);

    /**
     * Update an agent
     *
     * @param agentId agent ID
     * @param dto information needed to update the agent
     */
    void updateAgentById(String agentId, AgentUpdateDTO dto);

    /**
     * Update an agent accessible to the current user
     *
     * @param agentId agent ID
     * @param dto information needed to update the agent
     * @param userId current user ID
     */
    void updateAgentById(String agentId, AgentUpdateDTO dto, Long userId);

    /**
     * Update memory for an accessible agent by device MAC address
     *
     * @param macAddress device MAC address
     * @param dto agent memory
     * @param userId current user ID
     */
    void updateAgentMemoryByDeviceMacAddress(String macAddress, AgentMemoryDTO dto, Long userId);

    /**
     * Delete an agent accessible to the current user
     *
     * @param agentId agent ID
     * @param userId current user ID
     */
    void deleteAgentById(String agentId, Long userId);

    /**
     * Update an agent
     *
     * @param agentId agent ID
     * @param dto information needed to update the agent
     * @param createSnapshot whether to create a configuration snapshot
     */
    void updateAgentById(String agentId, AgentUpdateDTO dto, boolean createSnapshot);

    /**
     * Create an agent
     *
     * @param dto information needed to create the agent
     * @return created agent ID
     */
    String createAgent(AgentCreateDTO dto);


}
