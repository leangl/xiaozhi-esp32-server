package xiaozhi.common.page;

import java.io.Serializable;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Pagination utilities
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
@Data
@Schema(description = "Paginated data")
public class PageData<T> implements Serializable {
    @Schema(description = "Total record count")
    private int total;

    @Schema(description = "List data")
    private List<T> list;

    /**
     * Pagination
     *
     * @param list page data
     * @param total total record count
     */
    public PageData(List<T> list, long total) {
        this.list = list;
        this.total = (int) total;
    }
}
