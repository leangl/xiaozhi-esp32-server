package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * DTO for updating agent voiceprints
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintUpdateDTO {
    /**
     * Agent voiceprint ID
     */
    private String id;
    /**
     * Audio file ID
     */
    private String audioId;
    /**
     * Name of the person whose voiceprint is recorded
     */
    private String sourceName;
    /**
     * Description of the person whose voiceprint is recorded
     */
    private String introduce;
}
