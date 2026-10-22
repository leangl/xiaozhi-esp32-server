package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Update a device address book alias")
public class DeviceAddressBookAliasDTO {

    @NotBlank(message = "MAC address must not be empty")
    @Schema(description = "This device's MAC address")
    private String macAddress;

    @NotBlank(message = "Target MAC address must not be empty")
    @Schema(description = "Other device's MAC address")
    private String targetMac;

    @Schema(description = "Name used for the other device")
    private String alias;
}
