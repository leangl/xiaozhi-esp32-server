package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent_tag_relation")
@Schema(description = "Agent tag association")
public class AgentTagRelationEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "Agent ID")
    private String agentId;

    @Schema(description = "Tag ID")
    private String tagId;

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
