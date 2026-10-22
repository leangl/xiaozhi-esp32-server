package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Agent creation DTO
 * For agent creation only; id, agentCode, and sort are generated or assigned defaults by the system
 */
@Data
@Schema(description = "Agent creation object")
// The Chinese agent-name example is user-language sample data (customer service assistant).
public class AgentCreateDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Agent name", example = "客服助手")
    @NotBlank(message = "Agent name must not be empty")
    private String agentName;
}
