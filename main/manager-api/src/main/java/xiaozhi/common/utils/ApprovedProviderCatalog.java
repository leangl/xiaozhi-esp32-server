package xiaozhi.common.utils;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;

import org.springframework.beans.BeanWrapperImpl;

import xiaozhi.common.exception.RenException;
import xiaozhi.modules.model.entity.ModelConfigEntity;

/** Supported implementations, not a model-name or nationality filter. No network calls. */
public final class ApprovedProviderCatalog {
    private ApprovedProviderCatalog() {}

    private static final Map<String, Set<String>> TYPES = Map.of(
            "asr", Set.of("openai"), "llm", Set.of("openai", "ollama"),
            "vllm", Set.of("openai"), "tts", Set.of("openai"), "vad", Set.of("silero"),
            "memory", Set.of("nomem", "mem_local_short", "mem_report_only"),
            "intent", Set.of("nointent", "intent_llm", "function_call"),
            "rag", Set.of("ragflow"));
    private static final Set<String> FUNCTIONS = Set.of(
            "get_time", "get_lunar", "handle_exit_intent", "call_device", "change_role", "play_music",
            "hass_state", "hass_get_state", "hass_set_state", "hass_play_music", "search_from_ragflow");
    private static final Set<String> ENDPOINT_KEYS = Set.of("base_url", "api_url", "url", "endpoint", "host");
    private static final Set<String> PROXY_KEYS = Set.of("proxy", "http_proxy", "https_proxy", "all_proxy", "proxy_url");

    public static String normalize(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    public static boolean isSupportedType(String role, String type) {
        return TYPES.getOrDefault(normalize(role), Set.of()).contains(normalize(type));
    }

    public static boolean isSupportedPlugin(String code) {
        return FUNCTIONS.contains(normalize(code));
    }

    public static boolean isSupportedPluginConfig(String code) {
        return isSupportedPlugin(code) || "home_assistant".equals(normalize(code));
    }

    public static RenException unavailable(String role) {
        String safeRole = TYPES.containsKey(normalize(role)) ? normalize(role).toUpperCase(Locale.ROOT) : "Service";
        return new RenException(safeRole + " configuration is unavailable; select a supported provider with a reviewed endpoint");
    }

    public static void validate(String role, String providerCode, Map<String, ?> config) {
        String normalizedRole = normalize(role);
        Object suppliedType = config == null ? null : config.get("type");
        String type = suppliedType instanceof String value ? value : "";
        // Python's provider profile consumes exact implementation codes. Route/role
        // normalization must never reinterpret or rewrite persisted provider identity.
        if (!type.equals(normalize(type)) || !isSupportedType(normalizedRole, providerCode)
                || !normalize(providerCode).equals(type)) {
            throw unavailable(role);
        }
        try {
            for (Map.Entry<String, ?> entry : config.entrySet()) {
                String key = normalize(entry.getKey());
                Object value = entry.getValue();
                if (PROXY_KEYS.contains(key) && value != null && !value.toString().isBlank()) throw unavailable(role);
                if (ENDPOINT_KEYS.contains(key) && value != null && !value.toString().isBlank()) {
                    ApprovedServicePolicy.validateEndpoint(value.toString(),
                            type.equals("ollama") ? "memory" : normalizedRole.equals("rag") ? "tool" : normalizedRole);
                }
            }
            String endpointKey = switch (normalizedRole) {
                case "asr", "llm", "vllm", "rag" -> "base_url";
                case "tts" -> "api_url";
                default -> null;
            };
            if (endpointKey != null) {
                Object value = config.get(endpointKey);
                ApprovedServicePolicy.validateEndpoint(value == null ? null : value.toString(),
                        normalizedRole.equals("rag") ? "tool" : normalizedRole);
            }
            if (normalizedRole.equals("intent") && config.get("functions") != null) {
                Object functions = config.get("functions");
                Iterable<?> values = functions instanceof Iterable<?> list ? list
                        : functions instanceof Object[] array ? java.util.Arrays.asList(array)
                        : List.of(functions.toString().split(";"));
                for (Object function : values) {
                    if (function == null || !isSupportedPlugin(function.toString())) throw unavailable(role);
                }
            }
        } catch (RuntimeException rejected) {
            // No supplied type, URL, credential, nested exception or payload in diagnostics.
            throw unavailable(role);
        }
    }

    public static void validate(ModelConfigEntity model) {
        if (model == null || model.getConfigJson() == null) throw unavailable(null);
        validate(model.getModelType(), model.getConfigJson().getStr("type"), model.getConfigJson());
    }

    /** Configuration-only predicate for forward migration; deliberately ignores enabled state. */
    public static boolean isSupported(ModelConfigEntity model) {
        try { validate(model); return true; } catch (RuntimeException rejected) { return false; }
    }

    /** Selector predicate: both enabled and policy-valid, with no credentials in the result. */
    public static boolean isAvailable(ModelConfigEntity model) {
        return model != null && Integer.valueOf(1).equals(model.getIsEnabled()) && isSupported(model);
    }

    public static void validateSelection(String role, ModelConfigEntity model) {
        if (!isAvailable(model) || !normalize(role).equals(normalize(model.getModelType()))) throw unavailable(role);
    }

    /** Fixed property list shared by assistants, templates, update DTOs and historical snapshots. */
    public static void validateSelections(Object selections, Function<String, ModelConfigEntity> resolver) {
        var properties = Map.of("vadModelId", "vad", "asrModelId", "asr", "llmModelId", "llm",
                "vllmModelId", "vllm", "slmModelId", "llm", "ttsModelId", "tts",
                "memModelId", "memory", "intentModelId", "intent");
        var bean = new BeanWrapperImpl(selections);
        properties.forEach((property, role) -> {
            if (!bean.isReadableProperty(property)) return;
            Object value = bean.getPropertyValue(property);
            if (value == null || value.toString().isBlank()) return;
            ModelConfigEntity model = resolver.apply(value.toString());
            validateSelection(role, model);
            Object auxiliary = model.getConfigJson().get("llm");
            if (auxiliary != null && !auxiliary.toString().isBlank()) {
                validateSelection("llm", resolver.apply(auxiliary.toString()));
            }
        });
    }

    /** Recheck cached API configuration too; cache contents are not a policy authority. */
    public static void validateRuntimeConfig(Map<String, Object> config) {
        for (String role : TYPES.keySet()) {
            for (Map.Entry<String, Object> branch : config.entrySet()) {
                if (!normalize(branch.getKey()).equals(role)) continue;
                if (!(branch.getValue() instanceof Map<?, ?> models)) throw unavailable(role);
                for (Object value : models.values()) {
                    if (!(value instanceof Map<?, ?> raw)) throw unavailable(role);
                    @SuppressWarnings("unchecked") Map<String, ?> model = (Map<String, ?>) raw;
                    Object type = model.get("type");
                    validate(role, type == null ? null : type.toString(), model);
                }
            }
        }
        Object slm = config.get("SLM");
        if (slm instanceof Map<?, ?> models) {
            for (Object value : models.values()) {
                if (!(value instanceof Map<?, ?> raw)) throw unavailable("llm");
                @SuppressWarnings("unchecked") Map<String, ?> model = (Map<String, ?>) raw;
                Object type = model.get("type");
                validate("llm", type == null ? null : type.toString(), model);
            }
        }
        Object plugins = config.get("plugins");
        if (plugins instanceof Map<?, ?> entries) {
            for (var entry : entries.entrySet()) {
                if (!isSupportedPluginConfig(String.valueOf(entry.getKey()))) throw unavailable(null);
                Object params = entry.getValue();
                if (params instanceof String json) {
                    try { params = new cn.hutool.json.JSONObject(json); }
                    catch (RuntimeException invalid) { throw unavailable(null); }
                }
                if (params instanceof Map<?, ?> values) {
                    for (String key : PROXY_KEYS) {
                        Object proxy = values.get(key);
                        if (proxy != null && !proxy.toString().isBlank()) throw unavailable(null);
                    }
                    for (String key : ENDPOINT_KEYS) {
                        Object url = values.get(key);
                        if (url != null && !url.toString().isBlank()) {
                            try { ApprovedServicePolicy.validateEndpoint(url.toString(), "tool"); }
                            catch (RuntimeException rejected) { throw unavailable(null); }
                        }
                    }
                } else throw unavailable(null);
            }
        }
        Object contexts = config.get("context_providers");
        if (contexts instanceof Iterable<?> providers) {
            for (Object provider : providers) {
                Object url = provider instanceof Map<?, ?> values ? values.get("url")
                        : new BeanWrapperImpl(provider).getPropertyValue("url");
                try { ApprovedServicePolicy.validateEndpoint(url == null ? null : url.toString(), "context"); }
                catch (RuntimeException rejected) { throw unavailable(null); }
            }
        }
        Object mcp = config.get("mcp_endpoint");
        if (mcp != null && !mcp.toString().isBlank()) {
            try { ApprovedServicePolicy.validateEndpoint(mcp.toString(), "mcp"); }
            catch (RuntimeException rejected) { throw unavailable(null); }
        }
        Object voiceprint = config.get("voiceprint");
        if (voiceprint instanceof Map<?, ?> values) {
            Object url = values.get("url");
            try { ApprovedServicePolicy.validateEndpoint(url == null ? null : url.toString(), "voiceprint"); }
            catch (RuntimeException rejected) { throw unavailable(null); }
        }
    }
}
