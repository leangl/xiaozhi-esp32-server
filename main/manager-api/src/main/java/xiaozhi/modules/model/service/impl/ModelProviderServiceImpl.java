package xiaozhi.modules.model.service.impl;

import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import cn.hutool.json.JSONArray;
import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.ApprovedProviderCatalog;
import xiaozhi.modules.knowledge.dao.KnowledgeBaseDao;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.model.dao.ModelProviderDao;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.dto.ModelProviderDTO;
import xiaozhi.modules.model.entity.ModelProviderEntity;
import xiaozhi.modules.model.service.ModelProviderService;
import xiaozhi.modules.security.user.SecurityUser;

@Service
@AllArgsConstructor
public class ModelProviderServiceImpl extends BaseServiceImpl<ModelProviderDao, ModelProviderEntity>
        implements ModelProviderService {

    private final ModelProviderDao modelProviderDao;
    private final KnowledgeBaseDao knowledgeBaseDao;
    private final ModelConfigDao modelConfigDao;

    @Override
    public void validateSelection(String pluginId, Map<String, ?> params) {
        ModelProviderEntity plugin = modelProviderDao.selectById(pluginId);
        if (plugin != null) {
            if (!"plugin".equals(ApprovedProviderCatalog.normalize(plugin.getModelType()))
                    || !isSupportedProvider(plugin)) throw ApprovedProviderCatalog.unavailable(null);
            ApprovedProviderCatalog.validateRuntimeConfig(Map.of("plugins", Map.of(plugin.getProviderCode(), params == null ? Map.of() : params)));
            return;
        }
        // Dataset IDs are selectable only by their owner, never by a submitted provider alias.
        KnowledgeBaseEntity kb = knowledgeBaseDao.selectById(pluginId);
        UserDetail user = SecurityUser.getUser();
        if (kb == null || user == null || !user.getId().equals(kb.getCreator())
                || !Integer.valueOf(1).equals(kb.getStatus())) throw ApprovedProviderCatalog.unavailable(null);
        ApprovedProviderCatalog.validateSelection("rag", modelConfigDao.selectById(kb.getRagModelId()));
    }

    @Override
    public List<ModelProviderDTO> getPluginList() {
        // 1. Get plugins
        LambdaQueryWrapper<ModelProviderEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ModelProviderEntity::getModelType, "Plugin");
        List<ModelProviderEntity> providerEntities = modelProviderDao.selectList(queryWrapper);
        List<ModelProviderDTO> resultList = ConvertUtils.sourceToTarget(providerEntities.stream()
                .filter(this::isSupportedProvider).toList(), ModelProviderDTO.class);

        // 2. Append the current user's knowledge bases
        UserDetail userDetail = SecurityUser.getUser();
        if (userDetail != null && userDetail.getId() != null) {
            // Query the current user's knowledge bases
            LambdaQueryWrapper<KnowledgeBaseEntity> kbQueryWrapper = new LambdaQueryWrapper<>();
            kbQueryWrapper.eq(KnowledgeBaseEntity::getCreator, userDetail.getId());
            kbQueryWrapper.eq(KnowledgeBaseEntity::getStatus, 1); // Get enabled knowledge bases only
            List<KnowledgeBaseEntity> knowledgeBases = knowledgeBaseDao.selectList(kbQueryWrapper);

            // Convert knowledge bases to ModelProviderDTO and append them
            for (KnowledgeBaseEntity kb : knowledgeBases) {
                // Keep ownership/status checks even if a stale/misconfigured mapper returns extra rows.
                if (!userDetail.getId().equals(kb.getCreator()) || !Integer.valueOf(1).equals(kb.getStatus())) continue;
                var model = modelConfigDao.selectById(kb.getRagModelId());
                if (!ApprovedProviderCatalog.isAvailable(model)
                        || !"rag".equals(ApprovedProviderCatalog.normalize(model.getModelType()))) continue;
                ModelProviderDTO dto = new ModelProviderDTO();
                dto.setId(kb.getId());
                dto.setModelType("Rag");
                // Preserve the localized "[Knowledge base]" prefix in the user-visible plugin name.
                dto.setName("[知识库]" + kb.getName());
                dto.setProviderCode("ragflow"); // Assume all RAG providers use ragflow
                dto.setFields("[]");
                dto.setSort(0);
                dto.setCreateDate(kb.getCreatedAt());
                dto.setUpdateDate(kb.getUpdatedAt());
                dto.setCreator(0L);
                dto.setUpdater(0L);
                resultList.add(dto);
            }
        }

        // Schemas are selectable metadata, not a vehicle for platform credential defaults.
        resultList.forEach(dto -> dto.setFields(selectorFields(dto.getFields())));
        return resultList;
    }

    @Override
    public ModelProviderDTO getById(String id) {
        ModelProviderEntity entity = modelProviderDao.selectById(id);
        if (entity != null && !isSupportedProvider(entity)) return null;
        return ConvertUtils.sourceToTarget(entity, ModelProviderDTO.class);
    }

    @Override
    public List<ModelProviderDTO> getPluginListByIds(Collection<String> ids) {
        LambdaQueryWrapper<ModelProviderEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.in(ModelProviderEntity::getId, ids);
        queryWrapper.eq(ModelProviderEntity::getModelType, "Plugin");
        List<ModelProviderEntity> providerEntities = modelProviderDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(providerEntities.stream().filter(this::isSupportedProvider).toList(), ModelProviderDTO.class);
    }

    @Override
    public List<ModelProviderDTO> getListByModelType(String modelType) {

        QueryWrapper<ModelProviderEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("model_type", StringUtils.isBlank(modelType) ? "" : modelType);
        queryWrapper.orderByAsc("sort");
        List<ModelProviderEntity> providerEntities = modelProviderDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(providerEntities.stream().filter(this::isSupportedProvider).toList(), ModelProviderDTO.class);
    }

    @Override
    public PageData<ModelProviderDTO> getListPage(ModelProviderDTO modelProviderDTO, String page, String limit) {

        Map<String, Object> params = new HashMap<String, Object>();
        params.put(Constant.PAGE, page);
        params.put(Constant.LIMIT, limit);
        params.put(Constant.ORDER_FIELD, List.of("model_type", "sort"));
        params.put(Constant.ORDER, "asc");

        IPage<ModelProviderEntity> pageParam = getPage(params, null, true);

        QueryWrapper<ModelProviderEntity> wrapper = new QueryWrapper<ModelProviderEntity>();

        if (StringUtils.isNotBlank(modelProviderDTO.getModelType())) {
            wrapper.eq("model_type", modelProviderDTO.getModelType());
        }

        if (StringUtils.isNotBlank(modelProviderDTO.getName())) {
            wrapper.and(w -> w.like("name", modelProviderDTO.getName())
                    .or()
                    .like("provider_code", modelProviderDTO.getName()));
        }
        return getPageData(modelProviderDao.selectPage(pageParam, wrapper), ModelProviderDTO.class);
    }

    @Override
    public ModelProviderDTO add(ModelProviderDTO modelProviderDTO) {
        validateProvider(modelProviderDTO);
        UserDetail user = SecurityUser.getUser();
        modelProviderDTO.setCreator(user.getId());
        modelProviderDTO.setUpdater(user.getId());
        modelProviderDTO.setCreateDate(new Date());
        modelProviderDTO.setUpdateDate(new Date());
        // Strip surrounding double quotes from Fields

        modelProviderDTO.setFields(modelProviderDTO.getFields());
        ModelProviderEntity entity = ConvertUtils.sourceToTarget(modelProviderDTO, ModelProviderEntity.class);
        if (modelProviderDao.insert(entity) == 0) {
            throw new RenException(ErrorCode.ADD_DATA_FAILED);
        }

        return ConvertUtils.sourceToTarget(modelProviderDTO, ModelProviderDTO.class);
    }

    @Override
    public ModelProviderDTO edit(ModelProviderDTO modelProviderDTO) {
        validateProvider(modelProviderDTO);
        UserDetail user = SecurityUser.getUser();
        modelProviderDTO.setUpdater(user.getId());
        modelProviderDTO.setUpdateDate(new Date());
        if (modelProviderDao
                .updateById(ConvertUtils.sourceToTarget(modelProviderDTO, ModelProviderEntity.class)) == 0) {
            throw new RenException(ErrorCode.UPDATE_DATA_FAILED);
        }
        return ConvertUtils.sourceToTarget(modelProviderDTO, ModelProviderDTO.class);
    }

    @Override
    public void delete(String id) {
        if (modelProviderDao.deleteById(id) == 0) {
            throw new RenException(ErrorCode.DELETE_DATA_FAILED);
        }
    }

    @Override
    public void delete(List<String> ids) {
        if (modelProviderDao.deleteByIds(ids) == 0) {
            throw new RenException(ErrorCode.DELETE_DATA_FAILED);
        }
    }

    @Override
    public List<ModelProviderDTO> getList(String modelType, String providerCode) {
        QueryWrapper<ModelProviderEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("model_type", StringUtils.isBlank(modelType) ? "" : modelType);
        queryWrapper.eq("provider_code", StringUtils.isBlank(providerCode) ? "" : providerCode);
        List<ModelProviderEntity> providerEntities = modelProviderDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(providerEntities.stream().filter(this::isSupportedProvider).toList(), ModelProviderDTO.class);
    }

    private boolean isSupportedProvider(ModelProviderEntity entity) {
        return entity != null && (ApprovedProviderCatalog.isSupportedType(entity.getModelType(), entity.getProviderCode())
                || ("plugin".equals(ApprovedProviderCatalog.normalize(entity.getModelType()))
                        && ApprovedProviderCatalog.isSupportedPlugin(entity.getProviderCode())));
    }

    private void validateProvider(ModelProviderDTO dto) {
        if (dto == null || !isSupportedProvider(ConvertUtils.sourceToTarget(dto, ModelProviderEntity.class))) {
            throw ApprovedProviderCatalog.unavailable(dto == null ? null : dto.getModelType());
        }
    }

    private String selectorFields(String fields) {
        if (StringUtils.isBlank(fields)) return "[]";
        try {
            JSONArray result = new JSONArray(fields);
            for (Object item : result) {
                if (item instanceof cn.hutool.json.JSONObject field) {
                    field.remove("default");
                    field.remove("value");
                }
            }
            return result.toString();
        } catch (RuntimeException invalidSchema) {
            return "[]";
        }
    }
}
