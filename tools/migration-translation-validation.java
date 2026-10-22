import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import liquibase.Liquibase;
import liquibase.Scope;
import liquibase.database.DatabaseFactory;
import liquibase.database.jvm.JdbcConnection;
import liquibase.integration.spring.SpringResourceAccessor;
import org.springframework.core.io.DefaultResourceLoader;

/** Disposable-database validation only; never starts application services. */
class MigrationTranslationValidation {
    static String encode(String value) {
        return value == null ? "NULL" : Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    static void snapshot(Connection connection, Path output) throws Exception {
        Files.createDirectories(output);
        List<String> tables = new ArrayList<>();
        try (Statement statement = connection.createStatement();
             ResultSet rows = statement.executeQuery("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")) {
            while (rows.next()) tables.add(rows.getString(1));
        }
        Collections.sort(tables);
        List<String> summary = new ArrayList<>();
        for (String table : tables) {
            if (!table.matches("[A-Za-z0-9_]+")) throw new IllegalStateException("Unexpected table name");
            try (Statement statement = connection.createStatement();
                 ResultSet ddl = statement.executeQuery("SHOW CREATE TABLE `" + table + "`")) {
                ddl.next();
                Files.writeString(output.resolve(table + ".schema"), ddl.getString(2));
            }
            List<String> all = new ArrayList<>();
            List<String> stable = new ArrayList<>();
            try (Statement statement = connection.createStatement();
                 ResultSet rows = statement.executeQuery("SELECT * FROM `" + table + "`")) {
                ResultSetMetaData meta = rows.getMetaData();
                while (rows.next()) {
                    List<String> fullRow = new ArrayList<>();
                    List<String> stableRow = new ArrayList<>();
                    for (int i = 1; i <= meta.getColumnCount(); i++) {
                        String field = meta.getColumnName(i);
                        String value = encode(rows.getString(i));
                        fullRow.add(field + "=" + value);
                        if (!(table.equalsIgnoreCase("DATABASECHANGELOG") &&
                              (field.equalsIgnoreCase("DATEEXECUTED") || field.equalsIgnoreCase("DEPLOYMENT_ID")))) {
                            stableRow.add(field + "=" + value);
                        }
                    }
                    all.add(String.join("\t", fullRow));
                    stable.add(String.join("\t", stableRow));
                }
            }
            Collections.sort(all);
            Collections.sort(stable);
            Files.write(output.resolve(table + ".exact"), all);
            Files.write(output.resolve(table + ".stable"), stable);
            summary.add(table + "\t" + all.size());
        }
        Files.write(output.resolve("counts.tsv"), summary);
    }

    static void seed(Connection connection) throws Exception {
        // Entirely synthetic names/prompts/settings, including localized data and placeholders.
        try (Statement statement = connection.createStatement()) {
            int params = statement.executeUpdate("UPDATE sys_params SET param_value='synthetic-user-choice-{{name}}', remark='Synthetic edited setting' WHERE id=(SELECT id FROM (SELECT id FROM sys_params ORDER BY id LIMIT 1) chosen)");
            int templates = statement.executeUpdate("UPDATE ai_agent_template SET agent_name='Synthetic user name', system_prompt='Synthetic user prompt: \u4f60\u597d {{name}} {language}' WHERE id=(SELECT id FROM (SELECT id FROM ai_agent_template ORDER BY id LIMIT 1) chosen)");
            if (params != 1 || templates != 1) throw new IllegalStateException("Synthetic fixture was not installed");
        }
    }

    public static void main(String[] args) throws Exception {
        String databaseName = args[0];
        if (!databaseName.matches("migration_(baseline|current|upgrade)")) throw new IllegalArgumentException("Only disposable validation databases allowed");
        try (Connection connection = DriverManager.getConnection(
                "jdbc:mysql://migration-db:3306/" + databaseName + "?allowPublicKeyRetrieval=true&useSSL=false&serverTimezone=UTC&characterEncoding=UTF-8",
                "root", System.getenv("MYSQL_PWD"))) {
            try (Statement statement = connection.createStatement()) {
                // Stabilize SQL NOW()/CURRENT_TIMESTAMP seed values without changing SQL bytes.
                statement.execute("SET SESSION time_zone='+00:00'");
                statement.execute("SET SESSION timestamp=1770000000");
            }
            if (args[1].equals("update")) {
                var database = DatabaseFactory.getInstance().findCorrectDatabaseImplementation(new JdbcConnection(connection));
                var accessor = new SpringResourceAccessor(new DefaultResourceLoader());
                var liquibase = new Liquibase("classpath:/db/changelog/db.changelog-master.yaml", accessor, database);
                // SpringLiquibase installs this scope too. Existing-row checksum
                // validation asks Scope for its accessor rather than the instance.
                Scope.child(Map.of(Scope.Attr.resourceAccessor.name(), accessor), () -> {
                    liquibase.validate();
                    int pending = liquibase.listUnrunChangeSets(null, null).size();
                    System.out.println("PENDING_BEFORE=" + pending);
                    liquibase.update("");
                    liquibase.validate();
                    int after = liquibase.listUnrunChangeSets(null, null).size();
                    System.out.println("PENDING_AFTER=" + after);
                    if (after != 0) throw new IllegalStateException("Pending migrations remain");
                });
            } else if (args[1].equals("seed")) {
                seed(connection);
            } else if (!args[1].equals("snapshot")) {
                throw new IllegalArgumentException("Unknown mode");
            }
            snapshot(connection, Path.of(args[2]));
            System.out.println("SNAPSHOT=" + args[2]);
        }
    }
}
