package xiaozhi.modules.agent.vo;

import java.util.Date;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import xiaozhi.modules.agent.dto.AgentSnapshotDataDTO;

@Data
@Schema(description = "Agent configuration snapshot")
public class AgentSnapshotVO {
    private String id;
    private String agentId;
    @Schema(description = "Owner user ID, identifying the owner of the snapshot's agent")
    private Long userId;
    private Integer versionNo;
    private List<String> changedFields;
    private List<String> fieldOrder;
    private String source;
    @Schema(description = "Source snapshot ID for restore, populated only on the restored version")
    private String restoreFromSnapshotId;
    @Schema(description = "Source version for restore, populated only on the restored version")
    private Integer restoreFromVersionNo;
    @Schema(description = "Creator: operator who triggered this snapshot write")
    private Long creator;
    private Date createdAt;
    private AgentSnapshotDataDTO snapshotData;
    private AgentSnapshotDataDTO afterSnapshotData;
    @Schema(description = "Masked current configuration for restore preview, populated only by the details API")
    private AgentSnapshotDataDTO currentSnapshotData;
    @Schema(description = "Current configuration fingerprint for restore preview, populated only by the details API")
    private String currentStateToken;
}
