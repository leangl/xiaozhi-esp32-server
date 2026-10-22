package xiaozhi.common.utils;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.Date;

/**
 * Date handling
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public class DateUtils {
    /**
     * Date format (yyyy-MM-dd)
     */
    public final static String DATE_PATTERN = "yyyy-MM-dd";
    /**
     * Date-time format (yyyy-MM-dd HH:mm:ss)
     */
    public final static String DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss";
    public final static String DATE_TIME_MILLIS_PATTERN = "yyyy-MM-dd HH:mm:ss.SSS";


    /**
     * Format a date as yyyy-MM-dd
     *
     * @param date date
     * @return date formatted as yyyy-MM-dd
     */
    public static String format(Date date) {
        return format(date, DATE_PATTERN);
    }

    /**
     * Format a date as yyyy-MM-dd
     *
     * @param date date
     * @param pattern format, such as DateUtils.DATE_TIME_PATTERN
     * @return date formatted as yyyy-MM-dd
     */
    public static String format(Date date, String pattern) {
        if (date != null) {
            SimpleDateFormat df = new SimpleDateFormat(pattern);
            return df.format(date);
        }
        return null;
    }

    /**
     * Parse a date
     *
     * @param date date
     * @param pattern format, such as DateUtils.DATE_TIME_PATTERN
     * @return parsed Date
     */
    public static Date parse(String date, String pattern) {
        try {
            return new SimpleDateFormat(pattern).parse(date);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        return null;
    }


    public static String getDateTimeNow() {
        return getDateTimeNow(DATE_TIME_PATTERN);
    }

    public static String getDateTimeNow(String pattern) {
        return format(new Date(), pattern);
    }

    public static String millsToSecond(long mills) {
        return String.format("%.3f", mills / 1000.0);
    }

    /**
     * Get a short relative timestamp: just now below 10 seconds, seconds or hours ago, or full date-time after a week
     * @param date
     * @return
     */
    public static String getShortTime(Date date) {
        if (date == null) {
            return null;
        }
        // Convert Date to Instant
        LocalDateTime localDateTime = date.toInstant()
                // Get the system default time zone
                .atZone(ZoneId.systemDefault())
                // Convert to LocalDateTime
                .toLocalDateTime();
        // Current time
        LocalDateTime now = LocalDateTime.now();
        // Time difference in seconds
        long secondsBetween = ChronoUnit.SECONDS.between(localDateTime, now);

        // Existing Chinese UI labels: just now, seconds ago, minutes ago, hours ago, and days ago.
        // Preserve these localized values; changing them is not a maintainer-prose translation.
        if (secondsBetween <= 10) {
            return "刚刚";
        } else if (secondsBetween < 60) {
            return secondsBetween + "秒前";
        } else if (secondsBetween < 60 * 60) {
            return secondsBetween / 60 + "分钟前";
        } else if (secondsBetween < 86400) {
            return secondsBetween / 3600 + "小时前";
        } else if (secondsBetween < 604800) {
            return secondsBetween / 86400 + "天前";
        } else {
            // Show the full date-time after one week
            return format(date,DATE_TIME_PATTERN);
        }
    }
}
