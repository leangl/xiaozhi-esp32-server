package xiaozhi.modules.model.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;

import cn.hutool.json.JSONObject;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName(value = "ai_model_config", autoResultMap = true)
@Schema(description = "Model configuration table")
public class ModelConfigEntity {

    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "Model type (Memory/ASR/VAD/LLM/TTS)")
    private String modelType;

    @Schema(description = "Model code, such as AliLLM or DoubaoTTS")
    private String modelCode;

    @Schema(description = "Model name")
    private String modelName;

    @Schema(description = "Whether default (0: no, 1: yes)")
    private Integer isDefault;

    @Schema(description = "Whether enabled")
    private Integer isEnabled;

    @TableField(typeHandler = JacksonTypeHandler.class)
    @Schema(description = "Model configuration (JSON)")
    private JSONObject configJson;

    @Schema(description = "Official documentation link")
    private String docLink;

    @Schema(description = "Remarks")
    private String remark;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Updated by")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Update time")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Created by")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Creation time")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
