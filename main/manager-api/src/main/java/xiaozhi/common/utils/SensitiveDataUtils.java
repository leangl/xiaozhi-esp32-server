package xiaozhi.common.utils;

import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.apache.commons.lang3.StringUtils;

import cn.hutool.json.JSONObject;

/**
 * Sensitive data utilities
 */
public class SensitiveDataUtils {

    // Sensitive field names
    private static final Set<String> SENSITIVE_FIELDS = new HashSet<>(Arrays.asList(
            "api_key", "personal_access_token", "access_token", "token",
            "secret", "access_key_secret", "secret_key"));

    /**
     * Check whether a field is sensitive
     */
    public static boolean isSensitiveField(String fieldName) {
        return StringUtils.isNotBlank(fieldName) && SENSITIVE_FIELDS.contains(fieldName.toLowerCase());
    }

    /**
     * Mask the middle of a string
     */
    public static String maskMiddle(String value) {
        if (StringUtils.isBlank(value) || value.length() == 1) {
            return value;
        }

        int length = value.length();
        if (length <= 8) {
            // Keep the first and last two characters of short strings
            return value.substring(0, 2) + "****" + value.substring(length - 2);
        } else {
            // Keep the first and last four characters of long strings
            int maskLength = length - 8;
            StringBuilder maskBuilder = new StringBuilder();
            for (int i = 0; i < maskLength; i++) {
                maskBuilder.append('*');
            }
            return value.substring(0, 4) + maskBuilder.toString() + value.substring(length - 4);
        }
    }

    /**
     * Check whether a string is already masked
     */
    public static boolean isMaskedValue(String value) {
        if (StringUtils.isBlank(value)) {
            return false;
        }
        // Masked values contain at least four consecutive asterisks
        return value.contains("****");
    }

    /**
     * Process sensitive fields in a JSONObject
     */
    public static JSONObject maskSensitiveFields(JSONObject jsonObject) {
        if (jsonObject == null) {
            return null;
        }

        JSONObject result = new JSONObject();

        for (String key : jsonObject.keySet()) {
            Object value = jsonObject.get(key);

            if (SENSITIVE_FIELDS.contains(key.toLowerCase()) && value instanceof String) {
                result.set(key, maskMiddle((String) value));
            } else if (value instanceof JSONObject) {
                result.set(key, maskSensitiveFields((JSONObject) value));
            } else {
                result.set(key, value);
            }
        }

        return result;
    }

    /**
     * Compare sensitive fields in two JSONObjects
     * Compare sensitive fields such as api_key separately
     */
    public static boolean isSensitiveDataEqual(JSONObject original, JSONObject updated) {
        if (original == null && updated == null) {
            return true;
        }
        if (original == null || updated == null) {
            return false;
        }

        // Extract and compare specific sensitive fields
        return compareSpecificSensitiveFields(original, updated, "api_key") &&
                compareSpecificSensitiveFields(original, updated, "personal_access_token") &&
                compareSpecificSensitiveFields(original, updated, "access_token") &&
                compareSpecificSensitiveFields(original, updated, "token") &&
                compareSpecificSensitiveFields(original, updated, "secret") &&
                compareSpecificSensitiveFields(original, updated, "access_key_secret") &&
                compareSpecificSensitiveFields(original, updated, "secret_key");
    }

    /**
     * Compare specific sensitive fields in two JSON objects
     * Traverse the JSON object tree to find and compare the specified sensitive fields
     */
    private static boolean compareSpecificSensitiveFields(JSONObject original, JSONObject updated, String fieldName) {
        // Extract the specified sensitive fields from the original object
        Map<String, String> originalFields = new HashMap<>();
        extractSpecificSensitiveField(original, originalFields, fieldName, "");

        // Extract the specified sensitive fields from the updated object
        Map<String, String> updatedFields = new HashMap<>();
        extractSpecificSensitiveField(updated, updatedFields, fieldName, "");

        // Different field counts indicate additions or deletions
        if (originalFields.size() != updatedFields.size()) {
            return false;
        }

        // Compare each field's value
        for (Map.Entry<String, String> entry : originalFields.entrySet()) {
            String key = entry.getKey();
            String originalValue = entry.getValue();
            String updatedValue = updatedFields.get(key);

            if (updatedValue == null || !updatedValue.equals(originalValue)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Recursively extract sensitive fields with the specified names
     */
    private static void extractSpecificSensitiveField(JSONObject jsonObject, Map<String, String> fieldsMap,
            String targetFieldName, String parentPath) {
        if (jsonObject == null) {
            return;
        }

        for (String key : jsonObject.keySet()) {
            String fullPath = parentPath.isEmpty() ? key : parentPath + "." + key;
            Object value = jsonObject.get(key);

            if (value instanceof JSONObject) {
                // Recursively process nested JSON objects
                extractSpecificSensitiveField((JSONObject) value, fieldsMap, targetFieldName, fullPath);
            } else if (value instanceof String && key.equalsIgnoreCase(targetFieldName)) {
                // Save the path and value of each matching sensitive field
                fieldsMap.put(fullPath, (String) value);
            }
        }
    }
}
