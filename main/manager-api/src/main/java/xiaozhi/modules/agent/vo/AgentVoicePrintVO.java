package xiaozhi.modules.agent.vo;

import lombok.Data;

import java.util.Date;

/**
 * Agent voiceprint list VO
 */
@Data
public class AgentVoicePrintVO {

    /**
     * Primary key ID
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
    /**
     * Creation time
     */
    private Date createDate;
}
