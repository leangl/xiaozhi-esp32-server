package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysDictTypeDTO;
import xiaozhi.modules.sys.entity.SysDictTypeEntity;
import xiaozhi.modules.sys.vo.SysDictTypeVO;

/**
 * Data dictionary
 */
public interface SysDictTypeService extends BaseService<SysDictTypeEntity> {

    /**
     * Query paginated dictionary types
     *
     * @param params query parameters including pagination and filters
     * @return paginated dictionary types
     */
    PageData<SysDictTypeVO> page(Map<String, Object> params);

    /**
     * Get a dictionary type by ID
     *
     * @param id dictionary type ID
     * @return dictionary type
     */
    SysDictTypeVO get(Long id);

    /**
     * Save dictionary type information
     *
     * @param dto dictionary type DTO
     */
    void save(SysDictTypeDTO dto);

    /**
     * Update dictionary type information
     *
     * @param dto dictionary type DTO
     */
    void update(SysDictTypeDTO dto);

    /**
     * Delete dictionary types
     *
     * @param ids dictionary type IDs to delete
     */
    void delete(Long[] ids);

    /**
     * List all dictionary types
     *
     * @return dictionary type list
     */
    List<SysDictTypeVO> list(Map<String, Object> params);
}
