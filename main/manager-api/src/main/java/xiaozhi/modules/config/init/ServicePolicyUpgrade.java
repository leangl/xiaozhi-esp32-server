package xiaozhi.modules.config.init;

import java.util.ArrayList;
import java.util.List;

import org.springframework.context.annotation.DependsOn;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;

/** Runs after Liquibase and before configuration prewarming; never selects a replacement. */
@Service
@DependsOn("liquibase")
@RequiredArgsConstructor
@Slf4j
public class ServicePolicyUpgrade {
    private final ModelConfigDao models;
    private final JdbcTemplate jdbc;
    private final RedisUtils redis;
    private final PlatformTransactionManager transactions;

    public int apply() {
        List<String> cacheKeys = new ArrayList<>();
        Integer affected = new TransactionTemplate(transactions).execute(status -> {
            int count = 0;
            for (ModelConfigEntity model : models.selectList(null)) {
                cacheKeys.add(RedisKeys.getModelConfigById(model.getId()));
                if (!ApprovedProviderCatalog.isSupported(model)) {
                    // Update only activation flags; config, secrets, names, IDs and
                    // all assistant/history/snapshot references remain untouched.
                    if (!Integer.valueOf(0).equals(model.getIsEnabled())
                            || !Integer.valueOf(0).equals(model.getIsDefault())) {
                        var patch = new ModelConfigEntity();
                        patch.setId(model.getId());
                        patch.setIsEnabled(0);
                        patch.setIsDefault(0);
                        models.updateById(patch);
                    }
                    jdbc.update("INSERT INTO ai_service_remediation(model_id,reason_code) VALUES (?,?) "
                            + "ON DUPLICATE KEY UPDATE reason_code=VALUES(reason_code),resolved_at=NULL",
                            model.getId(), "APPROVED_REPLACEMENT_REQUIRED");
                    count++;
                } else {
                    jdbc.update("UPDATE ai_service_remediation SET resolved_at=CURRENT_TIMESTAMP "
                            + "WHERE model_id=? AND resolved_at IS NULL", model.getId());
                }
            }
            return count;
        });
        // Commit precedes invalidation. Failure blocks startup so stale cache
        // contents are never accepted as evidence of policy approval.
        cacheKeys.add(RedisKeys.getSysParamsKey());
        cacheKeys.add(RedisKeys.getServerConfigKey());
        redis.delete(cacheKeys);
        log.info("Service policy upgrade: unavailableModels={}; select explicit approved replacements. "
                + "No credentials, assistant IDs, conversation bodies or endpoints are logged.", affected);
        return affected == null ? 0 : affected;
    }
}
