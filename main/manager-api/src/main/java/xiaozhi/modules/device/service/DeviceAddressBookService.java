package xiaozhi.modules.device.service;

import java.util.List;
import java.util.Map;

import xiaozhi.modules.device.entity.DeviceAddressBookEntity;

public interface DeviceAddressBookService {

    /**
     * Get device address book entries
     */
    List<DeviceAddressBookEntity> getAddressBookList(String macAddress);

    /**
     * Get all device address books for the global cache
     */
    Map<String, Map<String, String>> getAllAddressBooks();

    /**
     * Update the alias
     */
    void updateAlias(String macAddress, String targetMac, String alias);

    /**
     * Update permissions
     */
    void updatePermission(String macAddress, String targetMac, Boolean hasPermission);

    /**
     * Add or update an address book entry
     */
    void saveOrUpdate(String macAddress, String targetMac, String alias, Boolean hasPermission);

    /**
     * Refresh the address book cache
     */
    void refreshCache();

    /**
     * Initiate a call by nickname
     * @param callerMac caller MAC address
     * @param nickname callee nickname
     * @param isAnswer whether answering (skips permission checks)
     */
    Map<String, Object> callByNickname(String callerMac, String nickname, boolean isAnswer);

    /**
     * Batch delete address book entries associated with devices
     */
    void deleteByMacAddresses(List<String> macAddresses);
}
