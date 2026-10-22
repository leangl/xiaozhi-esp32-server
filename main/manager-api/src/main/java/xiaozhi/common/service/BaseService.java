package xiaozhi.common.service;

import java.io.Serializable;
import java.util.Collection;

import com.baomidou.mybatisplus.core.conditions.Wrapper;

/**
 * Base service interface inherited by all service interfaces
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public interface BaseService<T> {
    Class<T> currentModelClass();

    /**
     * <p>
     * Insert one record using the field selection strategy
     * </p>
     *
     * @param entity entity instance
     */
    boolean insert(T entity);

    /**
     * <p>
     * Batch insert; not supported by Oracle or SQL Server
     * </p>
     *
     * @param entityList collection of entities
     */
    boolean insertBatch(Collection<T> entityList);

    /**
     * <p>
     * Batch insert; not supported by Oracle or SQL Server
     * </p>
     *
     * @param entityList collection of entities
     * @param batchSize insert batch size
     */
    boolean insertBatch(Collection<T> entityList, int batchSize);

    /**
     * <p>
     * Update selected fields by ID
     * </p>
     *
     * @param entity entity instance
     */
    boolean updateById(T entity);

    /**
     * <p>
     * Update records matching whereEntity
     * </p>
     *
     * @param entity entity instance
     * @param updateWrapper entity update wrapper
     *                      {@link com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper}
     */
    boolean update(T entity, Wrapper<T> updateWrapper);

    /**
     * <p>
     * Batch update by ID
     * </p>
     *
     * @param entityList collection of entities
     */
    boolean updateBatchById(Collection<T> entityList);

    /**
     * <p>
     * Batch update by ID
     * </p>
     *
     * @param entityList collection of entities
     * @param batchSize update batch size
     */
    boolean updateBatchById(Collection<T> entityList, int batchSize);

    /**
     * <p>
     * Query by ID
     * </p>
     *
     * @param id primary key ID
     */
    T selectById(Serializable id);

    /**
     * <p>
     * Delete by ID
     * </p>
     *
     * @param id primary key ID
     */
    boolean deleteById(Serializable id);

    /**
     * <p>
     * Batch delete by ID
     * </p>
     *
     * @param idList list of primary key IDs
     */
    boolean deleteBatchIds(Collection<? extends Serializable> idList);
}
