package xiaozhi.modules.voiceclone.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.voiceclone.dto.VoiceCloneDTO;
import xiaozhi.modules.voiceclone.dto.VoiceCloneResponseDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

/**
 * Voice cloning management
 */
public interface VoiceCloneService extends BaseService<VoiceCloneEntity> {

    /**
     * Paginated query
     */
    PageData<VoiceCloneEntity> page(Map<String, Object> params);

    /**
     * Save voice cloning data
     */
    void save(VoiceCloneDTO dto);

    /**
     * Batch delete
     */
    void delete(String[] ids);

    /**
     * Query voice clones by user ID
     * 
     * @param userId user ID
     * @return voice cloning list
     */
    List<VoiceCloneEntity> getByUserId(Long userId);

    /**
     * Query paginated voice clones with model and user names
     */
    PageData<VoiceCloneResponseDTO> pageWithNames(Map<String, Object> params);

    /**
     * Get voice cloning details with model and user names by ID
     */
    VoiceCloneResponseDTO getByIdWithNames(String id);

    /**
     * Query voice clones with model names by user ID
     */
    List<VoiceCloneResponseDTO> getByUserIdWithNames(Long userId);

    /**
     * Upload an audio file
     */
    void uploadVoice(String id, MultipartFile voiceFile) throws Exception;

    /**
     * Update the voice clone name
     */
    void updateName(String id, String name);

    /**
     * Get audio data
     */
    byte[] getVoiceData(String id);

    /**
     * Clone audio using Volcengine voice replication training
     * 
     * @param cloneId voice cloning record ID
     */
    void cloneAudio(String cloneId);
}
