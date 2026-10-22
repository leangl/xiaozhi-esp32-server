package xiaozhi.modules.voiceclone.service.impl;

import java.util.*;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.sys.dao.SysUserDao;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.voiceclone.dao.VoiceCloneDao;
import xiaozhi.modules.voiceclone.dto.VoiceCloneDTO;
import xiaozhi.modules.voiceclone.dto.VoiceCloneResponseDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;
import xiaozhi.modules.voiceclone.service.VoiceCloneService;

@Slf4j
@Service
@RequiredArgsConstructor
public class VoiceCloneServiceImpl extends BaseServiceImpl<VoiceCloneDao, VoiceCloneEntity>
        implements VoiceCloneService {

    private final ModelConfigService modelConfigService;
    private final SysUserService sysUserService;
    private final SysUserDao sysUserDao;
    private final ObjectMapper objectMapper;

    @Override
    public PageData<VoiceCloneEntity> page(Map<String, Object> params) {
        IPage<VoiceCloneEntity> page = baseDao.selectPage(
                getPage(params, "create_date", true),
                getWrapper(params));

        return new PageData<>(page.getRecords(), page.getTotal());
    }

    private QueryWrapper<VoiceCloneEntity> getWrapper(Map<String, Object> params) {
        String name = (String) params.get("name");
        String userId = (String) params.get("userId");

        QueryWrapper<VoiceCloneEntity> wrapper = new QueryWrapper<>();
        wrapper.eq(StringUtils.isNotBlank(userId), "user_id", userId);
        if (StringUtils.isNotBlank(name)) {
            wrapper.and(w -> w.like("name", name)
                    .or().eq("voice_id", name));
        }
        return wrapper;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void save(VoiceCloneDTO dto) {
        // There is no approved cloning adapter. Do not create apparently trainable records.
        throw cloningUnavailable();
    }

    @Override
    public void delete(String[] ids) {
        baseDao.deleteByIds(Arrays.asList(ids));
    }

    @Override
    public List<VoiceCloneEntity> getByUserId(Long userId) {
        QueryWrapper<VoiceCloneEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.orderByDesc("created_at");
        return baseDao.selectList(wrapper);
    }

    @Override
    public PageData<VoiceCloneResponseDTO> pageWithNames(Map<String, Object> params) {
        // Query paginated data first
        IPage<VoiceCloneEntity> page = baseDao.selectPage(
                getPage(params, "create_date", true),
                getWrapper(params));

        // Convert entity list to DTO list
        List<VoiceCloneResponseDTO> dtoList = convertToResponseDTOList(page.getRecords());

        return new PageData<>(dtoList, page.getTotal());
    }

    @Override
    public VoiceCloneResponseDTO getByIdWithNames(String id) {
        VoiceCloneEntity entity = baseDao.selectById(id);
        if (entity == null) {
            return null;
        }

        VoiceCloneResponseDTO dto = ConvertUtils.sourceToTarget(entity, VoiceCloneResponseDTO.class);

        // Set the model name
        if (StringUtils.isNotBlank(entity.getModelId())) {
            dto.setModelName(modelConfigService.getModelNameById(entity.getModelId()));
        }

        // Set the user name
        if (entity.getUserId() != null) {
            dto.setUserName(sysUserService.getByUserId(entity.getUserId()).getUsername());
        }
        
        // Ensure trainStatus is populated; the frontend uses it to identify cloned audio
        dto.setTrainStatus(entity.getTrainStatus());

        return dto;
    }

    @Override
    public List<VoiceCloneResponseDTO> getByUserIdWithNames(Long userId) {
        List<VoiceCloneEntity> entityList = getByUserId(userId);
        return convertToResponseDTOList(entityList);
    }

    /**
     * Convert VoiceCloneEntity list to VoiceCloneResponseDTO list
     */
    private List<VoiceCloneResponseDTO> convertToResponseDTOList(List<VoiceCloneEntity> entityList) {
        if (entityList == null || entityList.isEmpty()) {
            return new ArrayList<>();
        }

        List<VoiceCloneResponseDTO> dtoList = new ArrayList<>(entityList.size());

        // Get the user ID collection for name lookup
        Set<Long> userIdList = entityList.stream().map(VoiceCloneEntity::getUserId).collect(Collectors.toSet());
        List<SysUserEntity> userList = sysUserDao.selectList(new QueryWrapper<SysUserEntity>().in("id", userIdList));
        Map<Long, String> userMap = userList.stream().collect(Collectors.toMap(SysUserEntity::getId, SysUserEntity::getUsername));

        // Convert each entity to DTO
        for (VoiceCloneEntity entity : entityList) {
            VoiceCloneResponseDTO dto = ConvertUtils.sourceToTarget(entity, VoiceCloneResponseDTO.class);

            // Set the model name
            if (StringUtils.isNotBlank(entity.getModelId())) {
                dto.setModelName(modelConfigService.getModelNameById(entity.getModelId()));
            }

            // Set the user name
            if (entity.getUserId() != null) {
                dto.setUserName(userMap.get(entity.getUserId()));
            }
            
            // Ensure trainStatus is populated; the frontend uses it to identify cloned audio
            dto.setTrainStatus(entity.getTrainStatus());

            // Set whether audio data is present
            dto.setHasVoice(entity.getVoice() != null);

            dtoList.add(dto);
        }

        return dtoList;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void uploadVoice(String id, MultipartFile voiceFile) throws Exception {
        // Query the voice cloning record
        VoiceCloneEntity entity = baseDao.selectById(id);
        if (entity == null) {
            throw new RenException(ErrorCode.VOICE_CLONE_RECORD_NOT_EXIST);
        }

        // Read the audio file as bytes
        byte[] voiceData = voiceFile.getBytes();

        // Update the voice field
        entity.setVoice(voiceData);
        // Set training status to pending
        entity.setTrainStatus(0);

        // Save to the database
        baseDao.updateById(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateName(String id, String name) {
        // Query the voice cloning record
        VoiceCloneEntity entity = baseDao.selectById(id);
        if (entity == null) {
            throw new RenException(ErrorCode.VOICE_CLONE_RECORD_NOT_EXIST);
        }

        // Update the name
        entity.setName(name);
        baseDao.updateById(entity);
    }

    @Override
    public byte[] getVoiceData(String id) {
        VoiceCloneEntity entity = baseDao.selectById(id);
        if (entity == null) {
            return null;
        }
        return entity.getVoice();
    }

    @Override
    // @Transactional(rollbackFor = Exception.class)
    public void cloneAudio(String cloneId) {
        VoiceCloneEntity entity = baseDao.selectById(cloneId);
        if (entity == null) {
            throw new RenException(ErrorCode.VOICE_CLONE_RECORD_NOT_EXIST);
        }
        if (entity.getVoice() == null || entity.getVoice().length == 0) {
            throw new RenException(ErrorCode.VOICE_CLONE_AUDIO_NOT_UPLOADED);
        }

        // Existing recordings, provider IDs and historical training results remain untouched.
        throw cloningUnavailable();
    }

    private RenException cloningUnavailable() {
        return new RenException(ErrorCode.VOICE_CLONE_TRAINING_FAILED,
                "Voice cloning is unavailable; no replacement service has been approved");
    }
}
