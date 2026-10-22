package xiaozhi.modules.agent.entity;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent")
@Schema(description = "Agent information")
// The Chinese summarized-memory example is prompt sample data, retained with its original line break.
public class AgentEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Unique agent identifier")
    private String id;

    @Schema(description = "Owner user ID")
    private Long userId;

    @Schema(description = "Agent code")
    private String agentCode;

    @Schema(description = "Agent name")
    private String agentName;

    @Schema(description = "Speech recognition model ID")
    private String asrModelId;

    @Schema(description = "Voice activity detection ID")
    private String vadModelId;

    @Schema(description = "Large language model ID")
    private String llmModelId;

    @Schema(description = "Small language model identifier")
    private String slmModelId;

    @Schema(description = "VLLM model ID")
    private String vllmModelId;

    @Schema(description = "Speech synthesis model ID")
    private String ttsModelId;

    @Schema(description = "Voice ID")
    private String ttsVoiceId;

    @Schema(description = "Voice language")
    private String ttsLanguage;

    @Schema(description = "TTS volume")
    private Integer ttsVolume;

    @Schema(description = "TTS speech rate")
    private Integer ttsRate;

    @Schema(description = "TTS pitch")
    private Integer ttsPitch;

    @Schema(description = "Memory model ID")
    private String memModelId;

    @Schema(description = "Intent model ID")
    private String intentModelId;

    @Schema(description = "Chat history setting (0: off, 1: text only, 2: text and audio)")
    private Integer chatHistoryConf;

    @Schema(description = "Role configuration parameters")
    private String systemPrompt;

    @Schema(description = "Summarized memory", example = "构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹\n" +
            "根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;

    @Schema(description = "Language code")
    private String langCode;

    @Schema(description = "Interaction language")
    private String language;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Created by")
    private Long creator;

    @Schema(description = "Creation time")
    private Date createdAt;

    @Schema(description = "Updated by")
    private Long updater;

    @Schema(description = "Update time")
    private Date updatedAt;
}
