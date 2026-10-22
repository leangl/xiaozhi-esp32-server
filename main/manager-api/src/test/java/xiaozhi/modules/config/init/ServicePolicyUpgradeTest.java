package xiaozhi.modules.config.init;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.SimpleTransactionStatus;

import cn.hutool.json.JSONObject;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;

class ServicePolicyUpgradeTest {
    private final ModelConfigDao models = mock(ModelConfigDao.class);
    private final JdbcTemplate jdbc = mock(JdbcTemplate.class);
    private final RedisUtils redis = mock(RedisUtils.class);
    private final PlatformTransactionManager transactions = mock(PlatformTransactionManager.class);

    private ServicePolicyUpgrade subject() {
        when(transactions.getTransaction(any())).thenReturn(new SimpleTransactionStatus());
        return new ServicePolicyUpgrade(models, jdbc, redis, transactions);
    }

    private ModelConfigEntity model(String id, String type, String endpoint) {
        var model = new ModelConfigEntity();
        model.setId(id);
        model.setModelType("LLM");
        model.setModelName("Synthetic user choice");
        model.setIsDefault(1);
        model.setIsEnabled(1);
        model.setConfigJson(new JSONObject().set("type", type).set("base_url", endpoint)
                .set("api_key", "synthetic-secret"));
        return model;
    }

    @Test
    void quarantines_activation_only_and_commits_before_cache_invalidation() {
        var legacy = model("synthetic-legacy", "openai", "https://api.deepseek.com/v1");
        String config = legacy.getConfigJson().toString();
        when(models.selectList(isNull())).thenReturn(List.of(legacy));
        assertEquals(1, subject().apply());
        var patch = ArgumentCaptor.forClass(ModelConfigEntity.class);
        verify(models).updateById(patch.capture());
        assertEquals(legacy.getId(), patch.getValue().getId());
        assertEquals(0, patch.getValue().getIsEnabled());
        assertEquals(0, patch.getValue().getIsDefault());
        assertNull(patch.getValue().getConfigJson());
        assertNull(patch.getValue().getModelName());
        assertEquals(config, legacy.getConfigJson().toString());
        var order = inOrder(transactions, redis);
        order.verify(transactions).commit(any());
        order.verify(redis).delete(List.of("model:data:synthetic-legacy", "sys:params", "server:config"));
    }

    @Test
    void preserves_approved_choice_and_repeated_quarantine_is_not_an_overwrite() {
        var approved = model("synthetic-approved", "openai", "http://127.0.0.1:9000/v1");
        var retired = model("synthetic-retired", "retired-type", "https://unknown.example/");
        retired.setIsEnabled(0);
        retired.setIsDefault(0);
        when(models.selectList(isNull())).thenReturn(List.of(approved, retired));
        assertEquals(1, subject().apply());
        verify(models, never()).updateById(any(ModelConfigEntity.class));
        assertEquals(1, approved.getIsEnabled());
        assertEquals(1, approved.getIsDefault());
        verify(jdbc).update(contains("resolved_at=CURRENT_TIMESTAMP"), eq("synthetic-approved"));
    }

    @Test
    void database_failure_rolls_back_and_does_not_invalidate_or_hide_failure() {
        when(models.selectList(isNull())).thenThrow(new IllegalStateException("synthetic failure"));
        assertThrows(IllegalStateException.class, () -> subject().apply());
        verify(transactions).rollback(any());
        verifyNoInteractions(redis);
    }
}
