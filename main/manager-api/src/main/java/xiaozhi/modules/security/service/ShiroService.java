package xiaozhi.modules.security.service;

import xiaozhi.modules.security.entity.SysUserTokenEntity;
import xiaozhi.modules.sys.entity.SysUserEntity;

/**
 * Shiro interfaces
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public interface ShiroService {

    SysUserTokenEntity getByToken(String token);

    /**
     * Query a user by user ID
     *
     * @param userId
     */
    SysUserEntity getUser(Long userId);

}
