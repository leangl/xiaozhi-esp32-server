package xiaozhi.modules.sys.service;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.AdminPageUserDTO;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.vo.AdminPageUserVO;

/**
 * System user
 */
public interface SysUserService extends BaseService<SysUserEntity> {

    SysUserDTO getByUsername(String username);

    SysUserDTO getByUserId(Long userId);

    void save(SysUserDTO dto);

    /**
     * Delete the specified user and associated devices and agents
     * 
     * @param ids
     */
    void deleteById(Long ids);

    /**
     * Validate permission to change the password
     * 
     * @param userId user ID
     * @param passwordDTO password validation parameters
     */
    void changePassword(Long userId, PasswordDTO passwordDTO);

    /**
     * Change the password directly without validation
     * 
     * @param userId user ID
     * @param password password
     */
    void changePasswordDirectly(Long userId, String password);

    /**
     * Reset the password
     * 
     * @param userId user ID
     * @return randomly generated password meeting the requirements
     */
    String resetPassword(Long userId);

    /**
     * Administrator paginated user query
     * 
     * @param dto pagination query parameters
     * @return paginated users
     */
    PageData<AdminPageUserVO> page(AdminPageUserDTO dto);

    /**
     * Batch update user status
     * 
     * @param status user status
     * @param userIds array of user IDs
     */
    void changeStatus(Integer status, String[] userIds);

    /**
     * Get whether user registration is allowed
     * 
     * @return whether user registration is allowed
     */
    boolean getAllowUserRegister();
}
