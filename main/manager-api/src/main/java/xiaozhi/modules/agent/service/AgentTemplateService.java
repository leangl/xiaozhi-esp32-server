package xiaozhi.modules.agent.service;

import com.baomidou.mybatisplus.extension.repository.IRepository;

import xiaozhi.modules.agent.entity.AgentTemplateEntity;

/**
 * @author chenerlei
 * @description Database service for ai_agent_template (agent configuration templates)
 * @createDate 2025-03-22 11:48:18
 */
public interface AgentTemplateService extends IRepository<AgentTemplateEntity> {

    java.util.List<AgentTemplateEntity> getAvailableTemplates();

    /**
     * Get the default template
     * 
     * @return default template entity
     */
    AgentTemplateEntity getDefaultTemplate();

    /**
     * Update the model ID in the default template
     * 
     * @param modelType model type
     * @param modelId model ID
     */
    void updateDefaultTemplateModelId(String modelType, String modelId);

    /**
     * Reorder the remaining templates after deletion
     * 
     * @param deletedSort deleted template's sort value
     */
    void reorderTemplatesAfterDelete(Integer deletedSort);

    /**
     * Get the next available sort sequence number (the smallest unused number)
     * 
     * @return next available sort sequence number
     */
    Integer getNextAvailableSort();
}
