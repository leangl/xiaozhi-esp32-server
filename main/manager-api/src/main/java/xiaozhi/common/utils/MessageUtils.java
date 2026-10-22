package xiaozhi.common.utils;

import org.springframework.context.MessageSource;
import org.springframework.context.i18n.LocaleContextHolder;

/**
 * Internationalization
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public class MessageUtils {
    private static MessageSource messageSource;

    public static String getMessage(int code) {
        return getMessage(code, new String[0]);
    }

    public static String getMessage(int code, String... params) {
        if (messageSource == null) {
            // Initialize lazily to ensure the Spring context is fully initialized
            messageSource = (MessageSource) SpringContextUtils.getBean("messageSource");
        }
        return messageSource.getMessage(code + "", params, LocaleContextHolder.getLocale());
    }
}
