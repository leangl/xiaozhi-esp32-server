package xiaozhi.modules.sys.controller;

import java.util.Map;
import java.net.URI;
import java.net.http.WebSocket;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.annotation.LogOperation;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.config.RestTemplateConfig;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.common.utils.ApprovedServicePolicy;
import xiaozhi.common.validator.AssertUtils;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.common.validator.group.AddGroup;
import xiaozhi.common.validator.group.DefaultGroup;
import xiaozhi.common.validator.group.UpdateGroup;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.utils.WebSocketValidator;

/**
 * Parameter management
 *
 * @author Mark sunlightcs@gmail.com
 * @since 1.0.0
 */
@RestController
@RequestMapping("admin/params")
@Tag(name = "Parameter management")
@AllArgsConstructor
public class SysParamsController {
    private final SysParamsService sysParamsService;
    private final ConfigService configService;
    private final RestTemplate restTemplate;

    @GetMapping("page")
    @Operation(summary = "Pagination")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "Current page number, starting at 1", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.LIMIT, description = "Records per page", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.ORDER_FIELD, description = "Sort field", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = Constant.ORDER, description = "Sort direction (asc or desc)", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = "paramCode", description = "Parameter code or remarks", in = ParameterIn.QUERY, ref = "String")
    })
    @RequiresPermissions("sys:role:superAdmin")
    public Result<PageData<SysParamsDTO>> page(@Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageData<SysParamsDTO> page = sysParamsService.page(params);

        return new Result<PageData<SysParamsDTO>>().ok(page);
    }

    @GetMapping("{id}")
    @Operation(summary = "Information")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<SysParamsDTO> get(@PathVariable("id") Long id) {
        SysParamsDTO data = sysParamsService.get(id);

        return new Result<SysParamsDTO>().ok(data);
    }

    @PostMapping
    @Operation(summary = "Save")
    @LogOperation("Save")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> save(@RequestBody SysParamsDTO dto) {
        // Validate data
        ValidatorUtils.validateEntity(dto, AddGroup.class, DefaultGroup.class);

        validateWebSocketUrls(dto.getParamCode(), dto.getParamValue());
        validateOtaUrl(dto.getParamCode(), dto.getParamValue());
        validateMcpUrl(dto.getParamCode(), dto.getParamValue());
        validateVoicePrint(dto.getParamCode(), dto.getParamValue());
        sysParamsService.save(dto);
        configService.getConfig(false);
        return new Result<Void>();
    }

    @PutMapping
    @Operation(summary = "Update")
    @LogOperation("Update")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> update(@RequestBody SysParamsDTO dto) {
        // Validate data
        ValidatorUtils.validateEntity(dto, UpdateGroup.class, DefaultGroup.class);

        // Validate the WebSocket URL list
        validateWebSocketUrls(dto.getParamCode(), dto.getParamValue());

        // Validate the OTA URL
        validateOtaUrl(dto.getParamCode(), dto.getParamValue());

        // Validate the MCP URL
        validateMcpUrl(dto.getParamCode(), dto.getParamValue());

        // Validate the voiceprint URL
        validateVoicePrint(dto.getParamCode(), dto.getParamValue());

        // Validate MQTT secret length
        validateMqttSecretLength(dto.getParamCode(), dto.getParamValue());

        // Use special handling for system feature menu configuration
        if (Constant.SYSTEM_WEB_MENU.equals(dto.getParamCode())) {
            sysParamsService.updateSystemWebMenu(dto.getParamValue());
        } else {
            sysParamsService.update(dto);
        }
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * Validate the WebSocket URL list
     *
     * @param urls semicolon-separated WebSocket URLs
     * @return validation result
     */
    private void validateWebSocketUrls(String paramCode, String urls) {
        if (!paramCode.equals(Constant.SERVER_WEBSOCKET)) {
            return;
        }
        String[] wsUrls = urls.split("\\;");
        if (wsUrls.length == 0) {
            throw new RenException(ErrorCode.WEBSOCKET_URLS_EMPTY);
        }
        for (String url : wsUrls) {
            if (StringUtils.isNotBlank(url)) {
                // Validate the WebSocket URL format
                if (!WebSocketValidator.validateUrlFormat(url)) {
                    throw new RenException(ErrorCode.WEBSOCKET_URL_FORMAT_ERROR);
                }

                // Test the WebSocket connection
                try {
                    URI target = ApprovedServicePolicy.validateEndpoint(url, "mcp");
                    var client = RestTemplateConfig.directHttpClient(Duration.ofSeconds(5));
                    try {
                        WebSocket socket = client.newWebSocketBuilder().connectTimeout(Duration.ofSeconds(5))
                                .buildAsync(target, new WebSocket.Listener() {}).get(5, TimeUnit.SECONDS);
                        socket.abort();
                    } finally {
                        client.shutdownNow();
                    }
                } catch (Exception e) {
                    if (e instanceof InterruptedException) Thread.currentThread().interrupt();
                    throw new RenException(ErrorCode.WEBSOCKET_CONNECTION_FAILED);
                }
            }
        }
    }

    @PostMapping("/delete")
    @Operation(summary = "Delete")
    @LogOperation("Delete")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> delete(@RequestBody String[] ids) {
        // Validate data
        AssertUtils.isArrayEmpty(ids, "id");

        sysParamsService.delete(ids);
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * Validate the OTA URL
     */
    private void validateOtaUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_OTA)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }

        // Validate URL format
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException(ErrorCode.OTA_URL_PROTOCOL_ERROR);
        }
        if (!url.endsWith("/ota/")) {
            throw new RenException(ErrorCode.OTA_URL_FORMAT_ERROR);
        }

        try {
            ApprovedServicePolicy.validateEndpoint(url, "tool");
            // Send a GET request
            ResponseEntity<String> response = restTemplate.getForEntity(URI.create(url), String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.OTA_INTERFACE_ACCESS_FAILED);
            }
            // Check whether the response contains OTA information
            String body = response.getBody();
            if (body == null || !body.contains("OTA")) {
                throw new RenException(ErrorCode.OTA_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.OTA_INTERFACE_VALIDATION_FAILED);
        }
    }

    private void validateMcpUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_MCP_ENDPOINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }
        if (!hasServiceKey(url)) {
            throw new RenException(ErrorCode.MCP_URL_INVALID);
        }

        try {
            ApprovedServicePolicy.validateEndpoint(url, "mcp");
            // Send a GET request
            ResponseEntity<String> response = restTemplate.getForEntity(URI.create(url), String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.MCP_INTERFACE_ACCESS_FAILED);
            }
            // Check whether the response contains MCP information
            String body = response.getBody();
            if (body == null || !body.contains("success")) {
                throw new RenException(ErrorCode.MCP_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.MCP_INTERFACE_VALIDATION_FAILED);
        }
    }

    // Validate the voiceprint API URL
    private void validateVoicePrint(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_VOICE_PRINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            return;
        }
        if (!hasServiceKey(url)) {
            throw new RenException(ErrorCode.VOICEPRINT_URL_INVALID);
        }
        // Validate URL format
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException(ErrorCode.VOICEPRINT_URL_PROTOCOL_ERROR);
        }
        try {
            ApprovedServicePolicy.validateEndpoint(url, "voiceprint");
            // Send a GET request
            ResponseEntity<String> response = restTemplate.getForEntity(URI.create(url), String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_ACCESS_FAILED);
            }
            // Check response content
            String body = response.getBody();
            if (body == null || !body.contains("healthy")) {
                throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_FORMAT_ERROR);
            }
        } catch (Exception e) {
            throw new RenException(ErrorCode.VOICEPRINT_INTERFACE_VALIDATION_FAILED);
        }
    }

    private boolean hasServiceKey(String url) {
        try {
            String query = URI.create(url).getRawQuery();
            if (query == null) return false;
            var keys = java.util.Arrays.stream(query.split("&"))
                    .filter(pair -> pair.startsWith("key=")).map(pair -> pair.substring(4)).toList();
            return keys.size() == 1 && !java.net.URLDecoder.decode(
                    keys.getFirst(), java.nio.charset.StandardCharsets.UTF_8).isBlank();
        } catch (RuntimeException e) {
            return false;
        }
    }

    // Validate MQTT secret length and complexity
    private void validateMqttSecretLength(String paramCode, String secret) {
        if (!paramCode.equals(Constant.SERVER_MQTT_SECRET)) {
            return;
        }
        if (StringUtils.isBlank(secret) || secret.equals("null")) {
            throw new RenException(ErrorCode.MQTT_SECRET_EMPTY);
        }
        if (secret.length() < 8) {
            throw new RenException(ErrorCode.MQTT_SECRET_LENGTH_INSECURE);
        }
        // Check for both uppercase and lowercase letters
        if (!secret.matches(".*[a-z].*") || !secret.matches(".*[A-Z].*")) {
            throw new RenException(ErrorCode.MQTT_SECRET_CHARACTER_INSECURE);
        }
        // Reject weak passwords
        String[] weakPasswords = { "test", "1234", "admin", "password", "qwerty", "xiaozhi" };
        for (String weakPassword : weakPasswords) {
            if (secret.toLowerCase().contains(weakPassword)) {
                throw new RenException(ErrorCode.MQTT_SECRET_WEAK_PASSWORD);
            }
        }
    }
}
