package xiaozhi.modules.device.service;

import java.util.Date;
import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.dto.DevicePageUserDTO;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.vo.UserShowDeviceListVO;

public interface DeviceService extends BaseService<DeviceEntity> {
    /**
     * Get device online status data
     */
    String getDeviceOnlineData(String agentId);

    /**
     * Check whether the device is activated
     */
    DeviceReportRespDTO checkDeviceActive(String macAddress, String clientId,
            DeviceReportReqDTO deviceReport);

    /**
     * Get the user's devices for an agent
     */
    List<DeviceEntity> getUserDevices(Long userId, String agentId);

    /**
     * Get the user's devices for an agent, handling time zones
     */
    List<UserShowDeviceListVO> getUserDeviceList(Long userId, String agentId);

    /**
     * Unbind a device
     */
    void unbindDevice(Long userId, String deviceId);

    /**
     * Activate a device
     */
    Boolean deviceActivation(String agentId, String activationCode);

    /**
     * Delete all devices owned by this user
     * 
     * @param userId user ID
     */
    void deleteByUserId(Long userId);

    /**
     * Delete all devices associated with an agent
     * 
     * @param agentId agent ID
     */
    void deleteByAgentId(String agentId);

    /**
     * Get the device count for a user
     * 
     * @param userId user ID
     * @return device count
     */
    Long selectCountByUserId(Long userId);

    /**
     * Get a page of all device information
     *
     * @param dto pagination query parameters
     * @return paginated users
     */
    PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto);

    /**
     * Get device information by MAC address
     * 
     * @param macAddress MAC address
     * @return device information
     */
    DeviceEntity getDeviceByMacAddress(String macAddress);

    /**
     * Get the activation code by device ID
     * 
     * @param deviceId device ID
     * @return activation code
     */
    String geCodeByDeviceId(String deviceId);

    /**
     * Get the most recent connection time among this agent's devices
     * 
     * @param agentId agent ID
     * @return most recent device connection time
     */
    Date getLatestLastConnectionTime(String agentId);

    /**
     * Add a device manually
     */
    void manualAddDevice(Long userId, DeviceManualAddDTO dto);

    /**
     * Update device connection information
     */
    void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion);

    /**
     * Generate a WebSocket authentication token
     *
     * @param clientId client ID
     * @param username username (usually deviceId)
     * @return authentication token string
     * @throws Exception if token generation fails
     */
    String generateWebSocketToken(String clientId, String username) throws Exception;

    /**
     * Search devices by MAC address
     *
     * @param macAddress MAC address keyword
     * @param userId user ID
     * @return device list
     */
    List<DeviceEntity> searchDevicesByMacAddress(String macAddress, Long userId);

    /**
     * Get device tools
     */
    Object getDeviceTools(String deviceId);

    /**
     * Call a device tool
     */
    Object callDeviceTool(String deviceId, String toolName, Map<String, Object> arguments);

    }
