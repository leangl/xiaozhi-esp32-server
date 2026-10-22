package xiaozhi.modules.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

/**
 * Voiceprint recognition API response
 */
@Data
public class IdentifyVoicePrintResponse {
    /**
     * Best-matching voiceprint ID
     */
    @JsonProperty("speaker_id")
    private String speakerId;
    /**
     * Voiceprint score
     */
    private Double score;
}
