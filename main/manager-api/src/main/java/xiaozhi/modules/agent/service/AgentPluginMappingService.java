package xiaozhi.modules.agent.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.repository.IRepository;

import xiaozhi.modules.agent.entity.AgentPluginMapping;

/**
 * @description Database service for ai_agent_plugin_mapping (unique agent-to-plugin mappings)
 * @createDate 2025-05-25 22:33:17
 */
public interface AgentPluginMappingService extends IRepository<AgentPluginMapping> {

    void validateSelections(List<xiaozhi.modules.agent.dto.AgentUpdateDTO.FunctionInfo> functions);

    /**
     * Get plugin parameters by agent ID
     *
     * @param agentId
     * @return
     */
    List<AgentPluginMapping> agentPluginParamsByAgentId(String agentId);

    /**
     * Delete plugin parameters by agent ID
     *
     * @param agentId
     */
    void deleteByAgentId(String agentId);

    /**
     * Delete all agent plugin mappings for a plugin ID
     *
     * @param pluginId plugin ID
     */
    void deleteByPluginId(String pluginId);
}
