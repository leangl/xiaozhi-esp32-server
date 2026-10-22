import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;

import cn.hutool.json.JSONObject;
import liquibase.Liquibase;
import liquibase.Scope;
import liquibase.database.DatabaseFactory;
import liquibase.database.jvm.JdbcConnection;
import liquibase.integration.spring.SpringResourceAccessor;
import org.springframework.core.io.DefaultResourceLoader;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import xiaozhi.modules.config.init.ServicePolicyUpgrade;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;

/** Synthetic-only integration proof. No web server, API secret or external AI call. */
class ServiceMigrationValidation {
    static final String[] PRESERVED = {"sys_user", "ai_agent", "ai_device", "ai_agent_template",
        "ai_agent_chat_history", "ai_agent_chat_audio", "ai_agent_snapshot", "ai_tts_voice",
        "ai_agent_plugin_mapping", "ai_agent_context_provider"};

    static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }

    static String fingerprint(JdbcTemplate jdbc, String query) throws Exception {
        var rows = jdbc.query(query, (rs, row) -> {
            var fields = new ArrayList<String>();
            for (int i = 1; i <= rs.getMetaData().getColumnCount(); i++) {
                byte[] value = rs.getBytes(i);
                fields.add(value == null ? "NULL" : Base64.getEncoder().encodeToString(value));
            }
            return String.join("|", fields);
        });
        Collections.sort(rows);
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(String.join("\n", rows).getBytes(StandardCharsets.UTF_8)));
    }

    static Map<String, String> preserved(JdbcTemplate jdbc) throws Exception {
        var result = new TreeMap<String, String>();
        for (String table : PRESERVED) result.put(table, fingerprint(jdbc, "SELECT * FROM " + table));
        result.put("model-identities-config", fingerprint(jdbc,
            "SELECT id,model_type,model_code,model_name,config_json FROM ai_model_config"));
        result.put("historical-ledger", fingerprint(jdbc,
            "SELECT ID,AUTHOR,FILENAME,MD5SUM FROM DATABASECHANGELOG WHERE ID<>'202610210001'"));
        return result;
    }

    static void migrate(DriverManagerDataSource source, String root) throws Exception {
        try (var connection = source.getConnection()) {
            var accessor = new SpringResourceAccessor(new DefaultResourceLoader());
            var database = DatabaseFactory.getInstance().findCorrectDatabaseImplementation(new JdbcConnection(connection));
            var liquibase = new Liquibase(root, accessor, database);
            Scope.child(Map.of(Scope.Attr.resourceAccessor.name(), accessor), () -> {
                liquibase.validate();
                liquibase.update("");
                liquibase.validate();
                require(liquibase.listUnrunChangeSets(null, null).isEmpty(), "Pending migrations remain");
            });
        }
    }

    static ModelConfigEntity readModel(ResultSet rs, int row) throws SQLException {
        var model = new ModelConfigEntity();
        model.setId(rs.getString("id")); model.setModelType(rs.getString("model_type"));
        model.setModelCode(rs.getString("model_code")); model.setModelName(rs.getString("model_name"));
        model.setIsEnabled(rs.getInt("is_enabled")); model.setIsDefault(rs.getInt("is_default"));
        model.setConfigJson(new JSONObject(rs.getString("config_json")));
        return model;
    }

    static ServicePolicyUpgrade upgrade(JdbcTemplate jdbc, DriverManagerDataSource source) {
        var dao = (ModelConfigDao) Proxy.newProxyInstance(ModelConfigDao.class.getClassLoader(),
            new Class<?>[]{ModelConfigDao.class}, (proxy, method, args) -> {
                if (method.getName().equals("selectList")) return jdbc.query("SELECT * FROM ai_model_config", ServiceMigrationValidation::readModel);
                if (method.getName().equals("updateById")) {
                    var model = (ModelConfigEntity) args[0];
                    return jdbc.update("UPDATE ai_model_config SET is_enabled=?,is_default=? WHERE id=?",
                        model.getIsEnabled(), model.getIsDefault(), model.getId());
                }
                throw new UnsupportedOperationException("Unexpected fixture DAO method");
            });
        var redis = new RedisUtils() {
            @Override public void delete(Collection<String> keys) {
                require(keys.containsAll(List.of("sys:params", "server:config")), "Missing cache invalidation");
            }
        };
        return new ServicePolicyUpgrade(dao, jdbc, redis, new DataSourceTransactionManager(source));
    }

    static void seed(JdbcTemplate jdbc) {
        for (int family = 1; family <= 2; family++) {
            long user = 900100 + family;
            String agent = "policy-agent-" + family;
            jdbc.update("INSERT INTO sys_user(id,username,password,status) VALUES (?,?,?,1)", user, "policy-family-" + family, "synthetic-no-login");
            jdbc.update("INSERT INTO ai_agent(id,user_id,agent_name,llm_model_id,system_prompt) VALUES (?,?,?,?,?)",
                agent, user, "Synthetic assistant", "policy-legacy", "Synthetic retained context");
            jdbc.update("INSERT INTO ai_device(id,user_id,mac_address,agent_id) VALUES (?,?,?,?)",
                "policy-device-" + family, user, "02:00:00:00:00:0" + family, agent);
            jdbc.update("INSERT INTO ai_agent_chat_audio(id,audio) VALUES (?,?)", "policy-audio-" + family, new byte[]{0,1,2,3});
            jdbc.update("INSERT INTO ai_agent_chat_history(agent_id,session_id,chat_type,content,audio_id) VALUES (?,?,1,?,?)",
                agent, "policy-session-" + family, "Synthetic retained history", "policy-audio-" + family);
            jdbc.update("INSERT INTO ai_agent_snapshot(id,agent_id,user_id,version_no,snapshot_data) VALUES (?,?,?,1,?)",
                "policy-snapshot-" + family, agent, user, "{\"llmModelId\":\"policy-legacy\"}");
        }
        jdbc.update("INSERT INTO ai_model_config(id,model_type,model_code,model_name,is_enabled,is_default,config_json) VALUES "
            + "('policy-legacy','LLM','CustomAlias','Synthetic legacy',1,0,?)",
            "{\"type\":\"openai\",\"base_url\":\"https://api.deepseek.com/v1\",\"api_key\":\"synthetic-secret\"}");
        jdbc.update("UPDATE sys_params SET param_value='true' WHERE param_code='server.enable_mobile_register'");
    }

    public static void main(String[] args) throws Exception {
        require(args.length == 1 && Set.of("policy_fresh", "policy_upgrade").contains(args[0]), "Only disposable fixture databases allowed");
        var source = new DriverManagerDataSource("jdbc:mysql://policy-db:3306/" + args[0]
            + "?allowPublicKeyRetrieval=true&useSSL=false&serverTimezone=UTC&characterEncoding=UTF-8",
            "root", "disposable-validation-only");
        var jdbc = new JdbcTemplate(source);
        var service = upgrade(jdbc, source);
        if (args[0].equals("policy_upgrade")) {
            migrate(source, "classpath:/db/changelog/db.changelog-master.yaml");
            seed(jdbc);
            var before = preserved(jdbc);
            migrate(source, "classpath:/db/service-policy.changelog.yaml");
            service.apply();
            require(before.equals(preserved(jdbc)), "Preserved identities/history/audio/snapshot/checksum data changed");
            require(jdbc.queryForObject("SELECT is_enabled FROM ai_model_config WHERE id='policy-legacy'", Integer.class) == 0, "Legacy alias remains active");
            String repeated = fingerprint(jdbc, "SELECT * FROM ai_service_remediation");
            migrate(source, "classpath:/db/service-policy.changelog.yaml"); service.apply();
            require(repeated.equals(fingerprint(jdbc, "SELECT * FROM ai_service_remediation")), "Repeated upgrade is not idempotent");
            // Explicit operator replacement, not a migration-selected recipient.
            jdbc.update("UPDATE ai_model_config SET config_json=?,is_enabled=1 WHERE id='policy-legacy'",
                "{\"type\":\"openai\",\"base_url\":\"http://127.0.0.1:9000/v1\",\"api_key\":\"\"}");
            service.apply();
            require(jdbc.queryForObject("SELECT is_enabled FROM ai_model_config WHERE id='policy-legacy'", Integer.class) == 1, "Approved operator choice overwritten");
            require(jdbc.queryForObject("SELECT COUNT(*) FROM ai_service_remediation WHERE model_id='policy-legacy' AND resolved_at IS NOT NULL", Integer.class) == 1, "Remediation not resolved");
            System.out.println("PASS upgrade: two-family identities/history/audio/snapshots and historical checksums preserved; quarantine/retry/replacement verified");
        } else {
            migrate(source, "classpath:/db/service-policy.changelog.yaml"); service.apply();
            System.out.println("PASS fresh: forward root applied and supported catalog quarantined");
        }
        for (var model : jdbc.query("SELECT * FROM ai_model_config", ServiceMigrationValidation::readModel)) {
            require(!Integer.valueOf(1).equals(model.getIsEnabled()) || ApprovedProviderCatalog.isSupported(model), "Unsupported enabled model");
        }
        require("false".equals(jdbc.queryForObject("SELECT param_value FROM sys_params WHERE param_code='server.enable_mobile_register'", String.class)), "SMS flag not migrated");
    }
}
