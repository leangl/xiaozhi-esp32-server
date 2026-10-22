package xiaozhi.common.utils;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

import lombok.Data;

/**
 * Base class for all tree nodes
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
@Data
public class TreeNode<T> implements Serializable {

    /**
     * Primary key
     */
    private Long id;
    /**
     * Parent ID
     */
    private Long pid;
    /**
     * Child node list
     */
    private List<T> children = new ArrayList<>();

}
