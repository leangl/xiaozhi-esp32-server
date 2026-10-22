package xiaozhi.modules.sys.service.impl;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.common.utils.SM2Utils;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.sys.dao.SysParamsDao;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.entity.SysParamsEntity;
import xiaozhi.modules.sys.redis.SysParamsRedis;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * Parameter management
 */
@AllArgsConstructor
@Service
public class SysParamsServiceImpl extends BaseServiceImpl<SysParamsDao, SysParamsEntity> implements SysParamsService {
    private final SysParamsRedis sysParamsRedis;
    private final AgentPluginMappingService agentPluginMappingService;

    @Override
    public PageData<SysParamsDTO> page(Map<String, Object> params) {
        IPage<SysParamsEntity> page = baseDao.selectPage(
                getPage(params, null, false),
                getWrapper(params));

        return getPageData(page, SysParamsDTO.class);
    }

    @Override
    public List<SysParamsDTO> list(Map<String, Object> params) {
        List<SysParamsEntity> entityList = baseDao.selectList(getWrapper(params));

        return ConvertUtils.sourceToTarget(entityList, SysParamsDTO.class);
    }

    private QueryWrapper<SysParamsEntity> getWrapper(Map<String, Object> params) {
        String paramCode = (String) params.get("paramCode");

        QueryWrapper<SysParamsEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("param_type", 1);
        // Retired credentials remain inert in storage, not editable offerings.
        wrapper.notLikeRight("param_code", "aliyun.sms.");
        wrapper.nested(StringUtils.isNotBlank(paramCode), i -> i.like("param_code", paramCode)
                .or()
                .like("remark", paramCode));

        return wrapper;
    }

    @Override
    public SysParamsDTO get(Long id) {
        SysParamsEntity entity = baseDao.selectById(id);

        return ConvertUtils.sourceToTarget(entity, SysParamsDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(SysParamsDTO dto) {
        detectingSMSParameters(dto.getParamCode(), dto.getParamValue());
        validateParamValue(dto);

        SysParamsEntity entity = ConvertUtils.sourceToTarget(dto, SysParamsEntity.class);
        insert(entity);

        sysParamsRedis.set(entity.getParamCode(), entity.getParamValue());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(SysParamsDTO dto) {
        detectingSMSParameters(dto.getParamCode(), dto.getParamValue());
        validateParamValue(dto);
        SysParamsEntity entity = ConvertUtils.sourceToTarget(dto, SysParamsEntity.class);
        updateById(entity);

        sysParamsRedis.set(entity.getParamCode(), entity.getParamValue());
    }

    /**
     * Validate the parameter value type
     */
    private void validateParamValue(SysParamsDTO dto) {
        if (dto == null) {
            throw new RenException(ErrorCode.PARAM_VALUE_NULL);
        }

        if (StringUtils.isBlank(dto.getParamValue())) {
            throw new RenException(ErrorCode.PARAM_VALUE_NULL);
        }

        if (StringUtils.isBlank(dto.getValueType())) {
            throw new RenException(ErrorCode.PARAM_TYPE_NULL);
        }

        String valueType = dto.getValueType().toLowerCase();
        String paramValue = dto.getParamValue();

        switch (valueType) {
            case "string":
                break;
            case "array":
                break;
            case "number":
                try {
                    Double.parseDouble(paramValue);
                } catch (NumberFormatException e) {
                    throw new RenException(ErrorCode.PARAM_NUMBER_INVALID);
                }
                break;
            case "boolean":
                if (!"true".equalsIgnoreCase(paramValue) && !"false".equalsIgnoreCase(paramValue)) {
                    throw new RenException(ErrorCode.PARAM_BOOLEAN_INVALID);
                }
                break;
            case "json":
                try {
                    // First check for opening { and closing }
                    String trimmedValue = paramValue.trim();
                    if (!trimmedValue.startsWith("{") || !trimmedValue.endsWith("}")) {
                        throw new RenException(ErrorCode.PARAM_JSON_INVALID);
                    }
                    // Then try parsing JSON
                    JsonUtils.parseObject(paramValue, Object.class);
                } catch (Exception e) {
                    throw new RenException(ErrorCode.PARAM_JSON_INVALID);
                }
                break;
            default:
                throw new RenException(ErrorCode.PARAM_TYPE_INVALID);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(String[] ids) {
        // Delete Redis data
        List<String> paramCodeList = baseDao.getParamCodeList(ids);
        String[] paramCodes = paramCodeList.toArray(new String[paramCodeList.size()]);
        if (paramCodes.length > 0) {
            sysParamsRedis.delete(paramCodes);
        }

        // Delete
        deleteBatchIds(Arrays.asList(ids));
    }

    @Override
    public String getValue(String paramCode, Boolean fromCache) {
        String paramValue = null;
        if (fromCache) {
            paramValue = sysParamsRedis.get(paramCode);
            if (paramValue == null) {
                paramValue = baseDao.getValueByCode(paramCode);

                sysParamsRedis.set(paramCode, paramValue);
            }
        } else {
            paramValue = baseDao.getValueByCode(paramCode);
        }
        return paramValue;
    }

    @Override
    public <T> T getValueObject(String paramCode, Class<T> clazz) {
        String paramValue = getValue(paramCode, true);
        if (StringUtils.isNotBlank(paramValue)) {
            return JsonUtils.parseObject(paramValue, clazz);
        }

        try {
            return clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int updateValueByCode(String paramCode, String paramValue) {
        detectingSMSParameters(paramCode, paramValue);
        int count = baseDao.updateValueByCode(paramCode, paramValue);
        sysParamsRedis.set(paramCode, paramValue);
        return count;
    }

    @Override
    public void initServerSecret() {
        // Get the server secret
        String secretParam = getValue(Constant.SERVER_SECRET, false);
        if (StringUtils.isBlank(secretParam) || "null".equals(secretParam)) {
            String newSecret = UUID.randomUUID().toString();
            updateValueByCode(Constant.SERVER_SECRET, newSecret);
        }

        // Initialize the SM2 key pair
        initSM2KeyPair();
    }

    /**
     * Initialize the SM2 key pair
     */
    private void initSM2KeyPair() {
        // Get the SM2 public key
        String publicKey = getValue(Constant.SM2_PUBLIC_KEY, false);
        // Get the SM2 private key
        String privateKey = getValue(Constant.SM2_PRIVATE_KEY, false);

        // Generate a new pair if either public or private key is empty
        if (StringUtils.isBlank(publicKey) || StringUtils.isBlank(privateKey) || 
            "null".equals(publicKey) || "null".equals(privateKey)) {
            Map<String, String> keyPair = SM2Utils.createKey();
            String newPublicKey = keyPair.get(SM2Utils.KEY_PUBLIC_KEY);
            String newPrivateKey = keyPair.get(SM2Utils.KEY_PRIVATE_KEY);

            // Update the key pair in the database
            updateValueByCode(Constant.SM2_PUBLIC_KEY, newPublicKey);
            updateValueByCode(Constant.SM2_PRIVATE_KEY, newPrivateKey);
        }
    }

    /**
     * Check SMS parameter requirements
     * 
     * @param paramCode parameter code
     * @param paramValue parameter value
     * @return whether validation passed
     */
    private boolean detectingSMSParameters(String paramCode, String paramValue) {
        if (paramCode != null && paramCode.toLowerCase(java.util.Locale.ROOT).startsWith("aliyun.sms.")) {
            throw new RenException(ErrorCode.MOBILE_REGISTER_DISABLED);
        }
        // If this is not the phone registration parameter, skip other SMS checks and return true
        if (!Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue().equals(paramCode)) {
            return true;
        }
        // If SMS registration is being disabled, skip other SMS checks and return true
        if ("false".equalsIgnoreCase(paramValue)) {
            return true;
        }
        // No approved SMS replacement exists; do not accept an activation flag.
        throw new RenException(ErrorCode.MOBILE_REGISTER_DISABLED);
    }
    @Override
    public String getSystemWebMenu(boolean fromCache) {
        return getValue(Constant.SYSTEM_WEB_MENU, fromCache);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateSystemWebMenu(String configJson) {
        // Get the current configuration
        String currentConfig = getSystemWebMenu(false);
        Map<String, Object> currentMap = null;
        Map<String, Object> newMap = null;

        try {
            if (StringUtils.isNotBlank(currentConfig)) {
                currentMap = JsonUtils.parseMap(currentConfig);
            }
            if (StringUtils.isNotBlank(configJson)) {
                newMap = JsonUtils.parseMap(configJson);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.PARAM_JSON_INVALID);
        }

        // Check whether addressBook has been disabled
        if (currentMap != null && newMap != null) {
            Map<?, ?> currentFeatures = Map.class.cast(currentMap.get("features"));
            Map<?, ?> newFeatures = Map.class.cast(newMap.get("features"));

            if (currentFeatures != null && newFeatures != null) {
                Object currentAddressBookObj = currentFeatures.get("addressBook");
                Object newAddressBookObj = newFeatures.get("addressBook");

                Boolean currentEnabled = false;
                Boolean newEnabled = false;

                if (currentAddressBookObj instanceof Map<?, ?> currentAddressBook) {
                    Object enabled = currentAddressBook.get("enabled");
                    currentEnabled = enabled != null ? Boolean.class.cast(enabled) : false;
                }

                if (newAddressBookObj instanceof Map<?, ?> newAddressBook) {
                    Object enabled = newAddressBook.get("enabled");
                    newEnabled = enabled != null ? Boolean.class.cast(enabled) : false;
                }

                // Delete all call_device plugins if the feature changed from enabled to disabled
                if (Boolean.TRUE.equals(currentEnabled) && !Boolean.TRUE.equals(newEnabled)) {
                    agentPluginMappingService.deleteByPluginId("SYSTEM_PLUGIN_CALL_DEVICE");
                }
            }
        }

        // Update configuration
        updateValueByCode(Constant.SYSTEM_WEB_MENU, configJson);
    }
}
