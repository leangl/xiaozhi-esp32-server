package xiaozhi.common.xss;

import java.util.Collections;
import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

/**
 * XSS configuration options
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
@Data
@ConfigurationProperties(prefix = "renren.xss")
public class XssProperties {
    /**
     * Whether XSS filtering is enabled
     */
    private boolean enabled;
    /**
     * Excluded URL list
     */
    private List<String> excludeUrls = Collections.emptyList();
}
