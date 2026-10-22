package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Agent memory update DTO
 */
@Data
@Schema(description = "Agent memory update object")
// The Chinese memory example is prompt sample data; preserve its language and line break.
public class AgentMemoryDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Summarized memory", example = "构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹\n" +
            "根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;
}
