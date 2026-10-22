package xiaozhi.modules.agent.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "Agent snapshot pagination parameters")
public class AgentSnapshotPageDTO {
    @Schema(description = "Current page number, starting at 1", example = "1")
    private Integer page = 1;

    @Schema(description = "Records per page", example = "10")
    private Integer limit = 10;

    @Schema(description = "Version anchor: query historical snapshots at or below this version only", example = "20")
    private Integer maxVersionNo;

    public int pageOrDefault() {
        return page == null || page < 1 ? 1 : page;
    }

    public int limitOrDefault() {
        if (limit == null || limit < 1) {
            return 10;
        }
        return limit;
    }
}
