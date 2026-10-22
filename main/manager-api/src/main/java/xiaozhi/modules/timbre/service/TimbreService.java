package xiaozhi.modules.timbre.service;

import java.util.List;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.timbre.dto.TimbreDataDTO;
import xiaozhi.modules.timbre.dto.TimbrePageDTO;
import xiaozhi.modules.timbre.entity.TimbreEntity;
import xiaozhi.modules.timbre.vo.TimbreDetailsVO;

/**
 * Voice service interface
 * 
 * @author zjy
 * @since 2025-3-21
 */
public interface TimbreService extends BaseService<TimbreEntity> {
    /**
     * Get a page of voices for the specified TTS
     * 
     * @param dto pagination query parameters
     * @return paginated voices
     */
    PageData<TimbreDetailsVO> page(TimbrePageDTO dto);

    /**
     * Get voice details by ID
     * 
     * @param timbreId voice table ID
     * @return voice information
     */
    TimbreDetailsVO get(String timbreId);

    /**
     * Save voice information
     * 
     * @param dto data to save
     */
    void save(TimbreDataDTO dto);

    /**
     * Save voice information
     * 
     * @param timbreId ID to update
     * @param dto data to update
     */
    void update(String timbreId, TimbreDataDTO dto);

    /**
     * Batch delete voices
     * 
     * @param ids IDs of voices to delete
     */
    void delete(String[] ids);

    List<VoiceDTO> getVoiceNames(String ttsModelId, String voiceName);

    /**
     * Get the first valid configured language for a regular or cloned voice.
     *
     * @param id voice ID
     * @return default language, or null if the voice is absent or has no valid language
     */
    String getDefaultLanguageById(String id);

    /**
     * Get voice name by ID
     * 
     * @param id voice ID
     * @return voice name
     */
    String getTimbreNameById(String id);

    /**
     * Get voice information by voice code
     * 
     * @param ttsModelId voice model ID
     * @param voiceCode voice code
     * @return voice information
     */
    VoiceDTO getByVoiceCode(String ttsModelId, String voiceCode);
}
