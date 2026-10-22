package xiaozhi.modules.device.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_device_address_book")
@Schema(description = "Device address book")
public class DeviceAddressBookEntity {

    @TableId(type = IdType.INPUT)
    @Schema(description = "This device's MAC address")
    private String macAddress;

    @Schema(description = "Other device's MAC address")
    private String targetMac;

    @Schema(description = "Name used for the other device")
    private String alias;

    @Schema(description = "Whether calling is permitted")
    private Boolean hasPermission;

    @TableField(fill = FieldFill.INSERT)
    @Schema(description = "Created by")
    private Long creator;

    @TableField(fill = FieldFill.INSERT)
    @Schema(description = "Creation time")
    private Date createDate;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    @Schema(description = "Updated by")
    private Long updater;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    @Schema(description = "Update time")
    private Date updateDate;
}
