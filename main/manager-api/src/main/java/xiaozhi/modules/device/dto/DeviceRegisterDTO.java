package xiaozhi.modules.device.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

/**
 * Device registration headers
 * 
 * @author zjy
 * @since 2025-3-28
 */
@Setter
@Getter
@Schema(description = "Device registration headers")
public class DeviceRegisterDTO implements Serializable {

    @Schema(description = "MAC address")
    private String macAddress;

}
