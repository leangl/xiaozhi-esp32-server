package xiaozhi.modules.voiceclone.dao;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

/**
 * Voice cloning
 */
@Mapper
public interface VoiceCloneDao extends BaseMapper<VoiceCloneEntity> {
    /**
     * Get successfully trained voices for a user
     * 
     * @param modelId model ID
     * @param userId user ID
     * @return successfully trained voice list
     */
    List<VoiceDTO> getTrainSuccess(String modelId, Long userId);

}
