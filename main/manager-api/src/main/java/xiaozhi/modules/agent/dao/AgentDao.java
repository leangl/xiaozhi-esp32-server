package xiaozhi.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import org.apache.ibatis.annotations.Select;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.vo.AgentInfoVO;

@Mapper
public interface AgentDao extends BaseDao<AgentEntity> {
    /**
     * Get the agent's device count
     * 
     * @param agentId agent ID
     * @return device count
     */
    Integer getDeviceCountByAgentId(@Param("agentId") String agentId);

    /**
     * Look up the default agent for a device MAC address
     *
     * @param macAddress device MAC address
     * @return default agent information
     */
    @Select(" SELECT a.* FROM ai_device d " +
            " LEFT JOIN ai_agent a ON d.agent_id = a.id " +
            " WHERE d.mac_address = #{macAddress} " +
            " ORDER BY d.id DESC LIMIT 1")
    AgentEntity getDefaultAgentByMacAddress(@Param("macAddress") String macAddress);

    /**
     * Get agent details by ID, including plugins
     *
     * @param agentId agent ID
     */
    AgentInfoVO selectAgentInfoById(@Param("agentId") String agentId);

    /**
     * Lock the agent's main record to serialize configuration writes for the same agent
     *
     * @param agentId agent ID
     */
    AgentEntity selectByIdForUpdate(@Param("agentId") String agentId);

    /**
     * Write exactly the agent fields covered by the snapshot, including null values in the target snapshot.
     * Do not update ownership, creation metadata, or other fields outside the snapshot.
     *
     * @param agent agent with the target snapshot applied
     * @return affected row count
     */
    int updateSnapshotFields(@Param("agent") AgentEntity agent);
}
