package xiaozhi.modules.sys.service;


import java.util.function.Consumer;

/**
 * Define a system user utility to avoid circular dependencies with the user module
 * For example, users need all devices while devices need each owner's username
 * @author zjy
 * @since 2025-4-2
 */
public interface SysUserUtilService {
    /**
     * Assign the username
     * @param userId user ID
     * @param setter assignment method
     */
    void assignUsername( Long userId, Consumer<String> setter);
}
