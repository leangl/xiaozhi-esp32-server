package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * Administrator user pagination parameters DTO
 * 
 * @author zjy
 * @since 2025-3-21
 */
@Data
@Schema(description = "Administrator user pagination parameters DTO")
public class AdminPageUserDTO {

    @Schema(description = "Phone number")
    private String mobile;

    @Schema(description = "Page number")
    @Min(value = 0, message = "{sort.number}")
    private String page;

    @Schema(description = "Records to display")
    @Min(value = 0, message = "{sort.number}")
    private String limit;
}
