package xiaozhi.modules.agent.dto;

import java.util.Date;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import xiaozhi.modules.agent.dto.AgentTagDTO;

/**
 * Agent data transfer object
 * Transfers agent data between the service and controller layers
 */
@Data
@Schema(description = "Agent object")
// Chinese schema examples are user data: an assistant name/persona and a sample memory prompt, not API instructions.
public class AgentDTO {
    @Schema(description = "Agent code", example = "AGT_1234567890")
    private String id;

    @Schema(description = "Agent name", example = "客服助手")
    private String agentName;

    @Schema(description = "Speech synthesis model name", example = "tts_model_01")
    private String ttsModelName;

    @Schema(description = "Voice name", example = "voice_01")
    private String ttsVoiceName;

    @Schema(description = "Large language model name", example = "llm_model_01")
    private String llmModelName;

    @Schema(description = "Vision model name", example = "vllm_model_01")
    private String vllmModelName;

    @Schema(description = "Memory model ID", example = "mem_model_01")
    private String memModelId;

    @Schema(description = "Role configuration parameters", example = "你是一个专业的客服助手，负责回答用户问题并提供帮助")
    private String systemPrompt;

    @Schema(description = "Summarized memory", example = "构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹\n" +
            "根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;

    @Schema(description = "Last connection time", example = "2024-03-20 10:00:00")
    private Date lastConnectedAt;

    @Schema(description = "Device count", example = "10")
    private Integer deviceCount;

    @Schema(description = "Tag list")
    private List<AgentTagDTO> tags;
}
