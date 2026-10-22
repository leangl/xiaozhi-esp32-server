package xiaozhi.modules.model.dto;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * Basic LLM model display data
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class LlmModelBasicInfoDTO extends ModelBasicInfoDTO{
    private String type;
}
