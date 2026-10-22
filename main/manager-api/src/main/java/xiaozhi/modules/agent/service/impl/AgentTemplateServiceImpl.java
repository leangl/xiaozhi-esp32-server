package xiaozhi.modules.agent.service.impl;

import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.spring.repository.CrudRepository;

import xiaozhi.modules.agent.dao.AgentTemplateDao;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

/**
 * @author chenerlei
 * @description Database service implementation for ai_agent_template (agent configuration templates)
 * @createDate 2025-03-22 11:48:18
 */
@Service
@RequiredArgsConstructor
public class AgentTemplateServiceImpl extends CrudRepository<AgentTemplateDao, AgentTemplateEntity>
        implements AgentTemplateService {

    private final ModelConfigService modelConfigService;

    @Override
    public List<AgentTemplateEntity> getAvailableTemplates() {
        return list(new QueryWrapper<AgentTemplateEntity>().orderByAsc("sort")).stream().filter(template -> {
            try {
                ApprovedProviderCatalog.validateSelections(template, modelConfigService::getModelByIdFromCache);
                modelConfigService.validateVoiceSelection(template.getTtsModelId(), template.getTtsVoiceId());
                return true;
            } catch (RuntimeException unavailable) {
                return false;
            }
        }).toList();
    }

    @Override
    public boolean save(AgentTemplateEntity template) {
        ApprovedProviderCatalog.validateSelections(template, modelConfigService::getModelByIdFromCache);
        modelConfigService.validateVoiceSelection(template.getTtsModelId(), template.getTtsVoiceId());
        return super.save(template);
    }

    @Override
    public boolean updateById(AgentTemplateEntity template) {
        ApprovedProviderCatalog.validateSelections(template, modelConfigService::getModelByIdFromCache);
        if (template.getTtsModelId() != null || template.getTtsVoiceId() != null) {
            AgentTemplateEntity current = getById(template.getId());
            modelConfigService.validateVoiceSelection(template.getTtsModelId() == null && current != null ? current.getTtsModelId() : template.getTtsModelId(),
                    template.getTtsVoiceId() == null && current != null ? current.getTtsVoiceId() : template.getTtsVoiceId());
        }
        return super.updateById(template);
    }

    /**
     * Get the default template
     * 
     * @return default template entity
     */
    public AgentTemplateEntity getDefaultTemplate() {
        LambdaQueryWrapper<AgentTemplateEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByAsc(AgentTemplateEntity::getSort)
                .last("LIMIT 1");
        AgentTemplateEntity template = this.getOne(wrapper);
        if (template != null) {
            ApprovedProviderCatalog.validateSelections(template, modelConfigService::getModelByIdFromCache);
            modelConfigService.validateVoiceSelection(template.getTtsModelId(), template.getTtsVoiceId());
        }
        return template;
    }

    /**
     * Update the model ID in the default template
     * 
     * @param modelType model type
     * @param modelId model ID
     */
    @Override
    public void updateDefaultTemplateModelId(String modelType, String modelId) {
        modelConfigService.requireSelectable(modelId, modelType);
        modelType = modelType.toUpperCase(java.util.Locale.ROOT);
        // Do not update RAG models
        if (modelType.equals("RAG")) {
            return;
        }

        UpdateWrapper<AgentTemplateEntity> wrapper = new UpdateWrapper<>();
        switch (modelType) {
            case "ASR":
                wrapper.set("asr_model_id", modelId);
                break;
            case "VAD":
                wrapper.set("vad_model_id", modelId);
                break;
            case "LLM":
                wrapper.set("llm_model_id", modelId);
                break;
            case "TTS":
                wrapper.set("tts_model_id", modelId);
                wrapper.set("tts_voice_id", null);
                break;
            case "VLLM":
                wrapper.set("vllm_model_id", modelId);
                break;
            case "MEMORY":
                wrapper.set("mem_model_id", modelId);
                break;
            case "INTENT":
                wrapper.set("intent_model_id", modelId);
                break;
        }
        wrapper.ge("sort", 0);
        update(wrapper);
    }

    @Override
    public void reorderTemplatesAfterDelete(Integer deletedSort) {
        if (deletedSort == null) {
            return;
        }
        
        // Query templates with sort values greater than the deleted template
        UpdateWrapper<AgentTemplateEntity> updateWrapper = new UpdateWrapper<>();
        updateWrapper.gt("sort", deletedSort)
                    .setSql("sort = sort - 1");
        
        // Batch decrement those sort values by one
        this.update(updateWrapper);
    }

    @Override
    public Integer getNextAvailableSort() {
        // Query existing sort values in ascending order
        List<Integer> sortValues = baseMapper.selectList(new QueryWrapper<AgentTemplateEntity>())
                .stream()
                .map(AgentTemplateEntity::getSort)
                .filter(Objects::nonNull)
                .sorted()
                .collect(Collectors.toList());
        
        // Return 1 if no sort values exist
        if (sortValues.isEmpty()) {
            return 1;
        }
        
        // Find the smallest unused sequence number
        int expectedSort = 1;
        for (Integer sort : sortValues) {
            if (sort > expectedSort) {
                // Found a gap in the sequence
                return expectedSort;
            }
            expectedSort = sort + 1;
        }
        
        // Return the maximum sequence number plus one if no gap exists
        return expectedSort;
    }
}
