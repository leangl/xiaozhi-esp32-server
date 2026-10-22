package xiaozhi.common.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Data filtering annotation
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface DataFilter {
    /**
     * Table alias
     */
    String tableAlias() default "";

    /**
     * User ID
     */
    String userId() default "creator";

    /**
     * Department ID
     */
    String deptId() default "dept_id";

}
