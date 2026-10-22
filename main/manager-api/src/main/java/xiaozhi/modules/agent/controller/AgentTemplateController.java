package xiaozhi.modules.agent.controller;

import java.util.List;
import java.util.Map;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.common.utils.ResultUtils;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.agent.vo.AgentTemplateVO;

@Tag(name = "Agent template management")
@AllArgsConstructor
@RestController
@RequestMapping("/agent/template")
public class AgentTemplateController {
    
    private final AgentTemplateService agentTemplateService;
    
    @GetMapping("/page")
    @Operation(summary = "Get paginated templates")
    @RequiresPermissions("sys:role:superAdmin")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "Current page number, starting at 1", required = true),
            @Parameter(name = Constant.LIMIT, description = "Records per page", required = true),
            @Parameter(name = "agentName", description = "Template name, fuzzy match")
    })
    public Result<PageData<AgentTemplateVO>> getAgentTemplatesPage(
            @Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        
        // Create a pagination object
        int page = Integer.parseInt(params.getOrDefault(Constant.PAGE, "1").toString());
        int limit = Integer.parseInt(params.getOrDefault(Constant.LIMIT, "10").toString());
        Page<AgentTemplateEntity> pageInfo = new Page<>(page, limit);
        
        // Build query conditions
        QueryWrapper<AgentTemplateEntity> wrapper = new QueryWrapper<>();
        String agentName = (String) params.get("agentName");
        if (agentName != null && !agentName.isEmpty()) {
            wrapper.like("agent_name", agentName);
        }
        wrapper.orderByAsc("sort");
        
        // Execute the paginated query
        IPage<AgentTemplateEntity> pageResult = agentTemplateService.page(pageInfo, wrapper);
        
        // Convert to a VO list using ConvertUtils
        List<AgentTemplateVO> voList = ConvertUtils.sourceToTarget(pageResult.getRecords(), AgentTemplateVO.class);

        // Fix: construct PageData directly instead of using a no-argument constructor and setters
        PageData<AgentTemplateVO> pageData = new PageData<>(voList, pageResult.getTotal());

        return new Result<PageData<AgentTemplateVO>>().ok(pageData);
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get template details")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateVO> getAgentTemplateById(@PathVariable("id") String id) {
        AgentTemplateEntity template = agentTemplateService.getById(id);
        if (template == null) {
            return ResultUtils.error("Template does not exist");
        }
        
        // Convert to a VO using ConvertUtils
        AgentTemplateVO vo = ConvertUtils.sourceToTarget(template, AgentTemplateVO.class);
        
        return ResultUtils.success(vo);
    }
    
    @PostMapping
    @Operation(summary = "Create a template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateEntity> createAgentTemplate(@Valid @RequestBody AgentTemplateEntity template) {
        // Set the sort value to the next available sequence number
        template.setSort(agentTemplateService.getNextAvailableSort());
        
        boolean saved = agentTemplateService.save(template);
        if (saved) {
            return ResultUtils.success(template);
        } else {
            return ResultUtils.error("Failed to create template");
        }
    }
    
    @PutMapping
    @Operation(summary = "Update a template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateEntity> updateAgentTemplate(@Valid @RequestBody AgentTemplateEntity template) {
        boolean updated = agentTemplateService.updateById(template);
        if (updated) {
            return ResultUtils.success(template);
        } else {
            return ResultUtils.error("Failed to update template");
        }
    }
    
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<String> deleteAgentTemplate(@PathVariable("id") String id) {
        // Get the template and its sort value before deleting
        AgentTemplateEntity template = agentTemplateService.getById(id);
        if (template == null) {
            return ResultUtils.error("Template does not exist");
        }
        
        Integer deletedSort = template.getSort();
        
        // Perform the deletion
        boolean deleted = agentTemplateService.removeById(id);
        if (deleted) {
            // Reorder the remaining templates after successful deletion
            agentTemplateService.reorderTemplatesAfterDelete(deletedSort);
            return ResultUtils.success("Template deleted successfully");
        } else {
            return ResultUtils.error("Failed to delete template");
        }
    }
    
    
    // Add a batch deletion method with a different URL
    @PostMapping("/batch-remove")
    @Operation(summary = "Batch delete templates")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<String> batchRemoveAgentTemplates(@RequestBody List<String> ids) {
        boolean deleted = agentTemplateService.removeByIds(ids);
        if (deleted) {
            return ResultUtils.success("Batch deletion succeeded");
        } else {
            return ResultUtils.error("Failed to batch delete templates");
        }
    }
}
