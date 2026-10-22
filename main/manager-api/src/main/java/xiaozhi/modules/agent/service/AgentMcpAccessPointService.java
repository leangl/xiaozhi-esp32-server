package xiaozhi.modules.agent.service;


import java.util.List;

/**
 * Agent MCP access point service
 *
 * @author zjy
 */
public interface AgentMcpAccessPointService {
    /**
     * Get the agent's MCP access point URL
     * @param id agent ID
     * @return MCP access point URL
     */
   String getAgentMcpAccessAddress(String id);

    /**
     * Get tools available at the agent's MCP access point
     * @param id agent ID
     * @return tool list
     */
   List<String> getAgentMcpToolsList(String id);
}
