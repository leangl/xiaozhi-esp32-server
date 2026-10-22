package xiaozhi.modules.correctword.dto;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

@Data
@Schema(description = "Replacement word file creation DTO")
public class CorrectWordFileCreateDTO {

    @NotBlank(message = "File name must not be empty")
    @Schema(description = "File name")
    private String fileName;

    @NotEmpty(message = "Replacement word content must not be empty")
    @Schema(description = "Replacement words, each entry formatted as original|replacement")
    private List<String> content;

    @Schema(description = "File size in bytes, not exceeding 1MB")
    private Long fileSize;
}
