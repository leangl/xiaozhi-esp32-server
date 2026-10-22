package xiaozhi.modules.sys.dao;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.sys.entity.SysParamsEntity;

/**
 * Parameter management
 */
@Mapper
public interface SysParamsDao extends BaseDao<SysParamsEntity> {
    /**
     * Query a parameter value by code
     *
     * @param paramCode parameter code
     * @return parameter value
     */
    String getValueByCode(String paramCode);

    /**
     * Get parameter codes
     *
     * @param ids ids
     * @return parameter code list
     */
    List<String> getParamCodeList(String[] ids);

    /**
     * Update a parameter value by code
     *
     * @param paramCode parameter code
     * @param paramValue parameter value
     */
    int updateValueByCode(@Param("paramCode") String paramCode, @Param("paramValue") String paramValue);
}
