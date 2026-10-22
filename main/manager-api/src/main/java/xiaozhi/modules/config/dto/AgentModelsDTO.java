package xiaozhi.modules.config.dto;

import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
@Schema(description = "Agent model configuration request DTO")
public class AgentModelsDTO {

    @NotBlank(message = "Device MAC address must not be empty")
    @Schema(description = "Device MAC address")
    private String macAddress;

    @NotBlank(message = "Client ID must not be empty")
    @Schema(description = "Client ID")
    private String clientId;

    @NotNull(message = "Client-instantiated models must not be null")
    @Schema(description = "Models already instantiated by the client")
    private Map<String, String> selectedModule;
}
