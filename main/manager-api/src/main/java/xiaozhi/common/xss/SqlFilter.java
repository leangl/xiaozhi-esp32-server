package xiaozhi.common.xss;

import org.apache.commons.lang3.StringUtils;

import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;

/**
 * SQL filtering
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public class SqlFilter {

    /**
     * SQL injection filtering
     *
     * @param str string to validate
     */
    public static String sqlInject(String str) {
        if (StringUtils.isBlank(str)) {
            return null;
        }
        // Remove '|"|;|\ characters
        str = str.replace("'", "");
        str = str.replace("\"", "");
        str = str.replace(";", "");
        str = str.replace("\\", "");

        // Convert to lowercase
        str = str.toLowerCase();

        // Illegal characters
        String[] keywords = { "master", "truncate", "insert", "select", "delete", "update", "declare", "alter",
                "drop" };

        // Check for illegal characters
        for (String keyword : keywords) {
            if (str.contains(keyword)) {
                throw new RenException(ErrorCode.INVALID_SYMBOL);
            }
        }

        return str;
    }
}
