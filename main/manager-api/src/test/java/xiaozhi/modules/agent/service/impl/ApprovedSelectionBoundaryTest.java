package xiaozhi.modules.agent.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.List;
import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.dao.AgentTemplateDao;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentSnapshotService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;

class ApprovedSelectionBoundaryTest {
    @Test
    void assistantSelectionRejectsStaleProviderBeforeSnapshotsAndWrites() {
        AgentDao agents = mock(AgentDao.class);
        ModelConfigService models = mock(ModelConfigService.class);
        AgentSnapshotService snapshots = mock(AgentSnapshotService.class);
        AgentServiceImpl service = new AgentServiceImpl(agents, null, null, models, null, null, null, null,
                null, null, null, null, null, snapshots);
        AgentEntity prior = new AgentEntity();
        prior.setId("agent");
        prior.setLlmModelId("working");
        when(agents.selectByIdForUpdate("agent")).thenReturn(prior);
        when(models.getModelByIdFromCache("legacy")).thenReturn(model("coze"));
        AgentUpdateDTO update = new AgentUpdateDTO();
        update.setLlmModelId("legacy");
        assertThrows(RenException.class, () -> service.updateAgentById("agent", update));
        assertEquals("working", prior.getLlmModelId());
        verifyNoInteractions(snapshots);
        verify(agents, never()).updateById(any(AgentEntity.class));
    }

    @Test
    void templateCreateUpdateAndDefaultRejectUnavailableBeforeMutation() {
        ModelConfigService models = mock(ModelConfigService.class, CALLS_REAL_METHODS);
        AgentTemplateDao templates = mock(AgentTemplateDao.class);
        AgentTemplateServiceImpl service = new AgentTemplateServiceImpl(models);
        ReflectionTestUtils.setField(service, "baseMapper", templates);
        when(models.getModelByIdFromCache("legacy")).thenReturn(model("coze"));
        AgentTemplateEntity template = new AgentTemplateEntity();
        template.setId("template");
        template.setLlmModelId("legacy");
        assertThrows(RenException.class, () -> service.save(template));
        assertThrows(RenException.class, () -> service.updateById(template));
        assertThrows(RenException.class, () -> service.updateDefaultTemplateModelId("LLM", "legacy"));
        verifyNoInteractions(templates);
    }

    @Test
    void unavailableDefaultIsNotReplacedByAnotherTemplateAndListOmitsIt() {
        ModelConfigService models = mock(ModelConfigService.class);
        AgentTemplateDao templates = mock(AgentTemplateDao.class);
        AgentTemplateServiceImpl service = new AgentTemplateServiceImpl(models);
        ReflectionTestUtils.setField(service, "baseMapper", templates);
        AgentTemplateEntity stale = new AgentTemplateEntity();
        stale.setLlmModelId("legacy");
        AgentTemplateEntity approved = new AgentTemplateEntity();
        approved.setLlmModelId("approved");
        when(models.getModelByIdFromCache("legacy")).thenReturn(model("coze"));
        when(models.getModelByIdFromCache("approved")).thenReturn(model("openai"));
        when(templates.selectList(any())).thenReturn(List.of(stale, approved));
        assertEquals(List.of(approved), service.getAvailableTemplates());
        when(templates.selectOne(any(), anyBoolean())).thenReturn(stale);
        assertThrows(RenException.class, service::getDefaultTemplate);
    }

    private ModelConfigEntity model(String type) {
        ModelConfigEntity model = new ModelConfigEntity();
        model.setModelType("LLM");
        model.setIsEnabled(1);
        model.setConfigJson(new JSONObject().set("type", type).set("base_url", "http://localhost:9999/v1"));
        return model;
    }
}
