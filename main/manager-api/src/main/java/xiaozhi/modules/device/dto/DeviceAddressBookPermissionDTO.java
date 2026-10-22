package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Update device address book permissions")
public class DeviceAddressBookPermissionDTO {

    @NotBlank(message = "MAC address must not be empty")
    @Schema(description = "This device's MAC address")
    private String macAddress;

    @NotBlank(message = "Target MAC address must not be empty")
    @Schema(description = "Other device's MAC address")
    private String targetMac;

    @Schema(description = "Whether calling is permitted")
    private Boolean hasPermission;
}
