package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.entity.SysParamsEntity;

/**
 * Parameter management
 */
public interface SysParamsService extends BaseService<SysParamsEntity> {

    PageData<SysParamsDTO> page(Map<String, Object> params);

    List<SysParamsDTO> list(Map<String, Object> params);

    SysParamsDTO get(Long id);

    void save(SysParamsDTO dto);

    void update(SysParamsDTO dto);

    void delete(String[] ids);

    /**
     * Get a parameter value by code
     *
     * @param paramCode parameter code
     * @param fromCache whether to read from cache
     */
    String getValue(String paramCode, Boolean fromCache);

    /**
     * Get a parameter value as an object by code
     *
     * @param paramCode parameter code
     * @param clazz target object class
     */
    <T> T getValueObject(String paramCode, Class<T> clazz);

    /**
     * Update a parameter value by code
     *
     * @param paramCode parameter code
     * @param paramValue parameter value
     */
    int updateValueByCode(String paramCode, String paramValue);

    /**
     * Initialize the server secret
     */
    void initServerSecret();

    /**
     * Get system feature menu configuration
     *
     * @param fromCache whether to read from cache
     * @return system feature menu configuration JSON
     */
    String getSystemWebMenu(boolean fromCache);

    /**
     * Update system feature menu configuration, automatically cleaning up related plugins
     *
     * @param configJson new system feature menu configuration JSON
     */
    void updateSystemWebMenu(String configJson);
}
