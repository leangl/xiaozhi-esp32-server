package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * DTO for saving agent voiceprints
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintSaveDTO {
    /**
     * Associated agent ID
     */
    private String agentId;
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
