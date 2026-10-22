package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysDictDataDTO;
import xiaozhi.modules.sys.entity.SysDictDataEntity;
import xiaozhi.modules.sys.vo.SysDictDataItem;
import xiaozhi.modules.sys.vo.SysDictDataVO;

/**
 * Data dictionary
 */
public interface SysDictDataService extends BaseService<SysDictDataEntity> {

    /**
     * Query paginated dictionary data
     *
     * @param params query parameters including pagination and filters
     * @return paginated dictionary data
     */
    PageData<SysDictDataVO> page(Map<String, Object> params);

    /**
     * Get a dictionary entry by ID
     *
     * @param id unique dictionary entry ID
     * @return dictionary entry details
     */
    SysDictDataVO get(Long id);

    /**
     * Save a new dictionary entry
     *
     * @param dto dictionary entry creation DTO
     */
    void save(SysDictDataDTO dto);

    /**
     * Update a dictionary entry
     *
     * @param dto dictionary entry update DTO
     */
    void update(SysDictDataDTO dto);

    /**
     * Delete dictionary entries
     *
     * @param ids IDs of dictionary entries to delete
     */
    void delete(Long[] ids);

    /**
     * Delete dictionary data by dictionary type ID
     *
     * @param dictTypeId dictionary type ID
     */
    void deleteByTypeId(Long dictTypeId);

    /**
     * Get dictionary data by dictionary type
     *
     * @param dictType dictionary type
     * @return dictionary data list
     */
    List<SysDictDataItem> getDictDataByType(String dictType);

}
