package xiaozhi.modules.llm.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import org.springframework.web.client.RestTemplate;
import cn.hutool.json.JSONObject;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;

class ApprovedLlmBoundaryTest {
    @Test
    void legacyOrAliasedModelCannotSendSummaryOrTitleEvenWithDefaultAvailable() {
        ModelConfigService models = mock(ModelConfigService.class);
        var service = new OpenAIStyleLLMServiceImpl();
        ReflectionTestUtils.setField(service, "modelConfigService", models);
        RestTemplate http = (RestTemplate) ReflectionTestUtils.getField(service, "restTemplate");
        var network = MockRestServiceServer.bindTo(http).build(); // Zero expectations: any request fails this test.
        ModelConfigEntity approved = model("openai", "http://localhost:9999/v1");
        approved.setIsDefault(1);
        when(models.getEnabledModelsByType("LLM")).thenReturn(List.of(approved));
        for (ModelConfigEntity invalid : List.of(model("coze", "http://localhost:9999/v1"),
                model("openai", "https://unknown.example/secret"))) {
            when(models.getModelByIdFromCache("stale")).thenReturn(invalid);
            assertFalse(service.isAvailable("stale"));
            assertTrue(service.generateSummaryWithModel("synthetic-conversation", "stale").contains("unavailable"));
            assertTrue(service.generateSummaryWithHistory("synthetic-conversation", "memory", null, "stale").contains("unavailable"));
            assertNull(service.generateTitle("synthetic-conversation", "stale"));
        }
        network.verify();
    }

    @Test
    void explicitApprovedModelWorksWithoutSilentlySelectingAnotherDefault() {
        ModelConfigService models = mock(ModelConfigService.class);
        var service = new OpenAIStyleLLMServiceImpl();
        ReflectionTestUtils.setField(service, "modelConfigService", models);
        when(models.getModelByIdFromCache("explicit")).thenReturn(model("openai", "http://localhost:9999/v1"));
        when(models.getEnabledModelsByType("LLM")).thenReturn(List.of(model("openai", "http://localhost:9999/v1")));
        assertFalse(service.isAvailable()); // An enabled nondefault is not an implicit replacement.
        RestTemplate http = (RestTemplate) ReflectionTestUtils.getField(service, "restTemplate");
        var network = MockRestServiceServer.bindTo(http).build();
        network.expect(requestTo("http://localhost:9999/v1/chat/completions"))
                .andRespond(withSuccess("{\"choices\":[{\"message\":{\"content\":\"synthetic-summary\"}}]}", org.springframework.http.MediaType.APPLICATION_JSON));
        assertEquals("synthetic-summary", service.generateSummaryWithModel("synthetic-conversation", "explicit"));
        network.verify();
    }

    private ModelConfigEntity model(String type, String url) {
        ModelConfigEntity model = new ModelConfigEntity();
        model.setModelType("LLM");
        model.setIsEnabled(1);
        model.setIsDefault(0);
        model.setConfigJson(new JSONObject().set("type", type).set("base_url", url).set("model_name", "synthetic")
                .set("api_key", "synthetic-key"));
        return model;
    }
}
