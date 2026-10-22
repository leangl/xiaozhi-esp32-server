package xiaozhi.modules.device.service.impl;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Instant;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.vo.UserShowDeviceListVO;
import xiaozhi.modules.security.config.WebMvcConfig;

@DisplayName("Device time serialization regression tests")
class DeviceTimeSerializationTest {

    @ParameterizedTest(name = "Browser time zone {0}")
    @ValueSource(strings = { "Asia/Shanghai", "America/Sao_Paulo" })
    @DisplayName("#3280 Binding and last connection times represent the same instant in every browser time zone")
    void serializedDeviceTimesDescribeTheSameInstantAcrossBrowserTimeZones(String browserTimeZone) {
        Instant connectedAt = Instant.parse("2026-07-10T13:21:42Z");
        DeviceEntity entity = new DeviceEntity();
        entity.setCreateDate(Date.from(connectedAt));
        entity.setLastConnectedAt(Date.from(connectedAt));

        DeviceServiceImpl deviceService = serviceReturning(entity);
        UserShowDeviceListVO device = deviceService.getUserDeviceList(1L, "agent-id").getFirst();

        ObjectMapper objectMapper = new WebMvcConfig().jackson2HttpMessageConverter().getObjectMapper();
        JsonNode payload = objectMapper.valueToTree(device);
        Instant createDate = Instant.ofEpochMilli(
                Long.parseLong(payload.path("createDateTimestamp").asText()));
        Instant lastConnectedAt = Instant.ofEpochMilli(
                Long.parseLong(payload.path("lastConnectedAtTimestamp").asText()));
        ZoneId browserZone = ZoneId.of(browserTimeZone);

        assertAll(
                () -> assertTrue(payload.path("createDateTimestamp").isTextual(),
                        "Long timestamps must follow the existing JSON contract and serialize as strings"),
                () -> assertTrue(payload.path("lastConnectedAtTimestamp").isTextual(),
                        "Long timestamps must follow the existing JSON contract and serialize as strings"),
                () -> assertEquals(connectedAt, createDate,
                        "createDateTimestamp must preserve the source instant"),
                () -> assertEquals(connectedAt, lastConnectedAt,
                        "lastConnectedAtTimestamp must preserve the source instant"),
                () -> assertEquals(lastConnectedAt.atZone(browserZone).toLocalDateTime(),
                        createDate.atZone(browserZone).toLocalDateTime(),
                        "Binding and last connection times must display the same local time in the same browser"),
                () -> assertTrue(payload.path("createDate").isTextual(),
                        "The createDate compatibility field must be retained"));
    }

    @Test
    @DisplayName("Both legacy and new fields remain null when time is absent")
    void nullDeviceTimesRemainNull() {
        DeviceEntity entity = new DeviceEntity();
        DeviceServiceImpl deviceService = serviceReturning(entity);

        UserShowDeviceListVO device = deviceService.getUserDeviceList(1L, "agent-id").getFirst();
        ObjectMapper objectMapper = new WebMvcConfig().jackson2HttpMessageConverter().getObjectMapper();
        JsonNode payload = objectMapper.valueToTree(device);

        assertAll(
                () -> assertTrue(payload.path("createDateTimestamp").isNull()),
                () -> assertTrue(payload.path("lastConnectedAtTimestamp").isNull()),
                () -> assertTrue(payload.path("createDate").isNull()));
    }

    @ParameterizedTest(name = "Automatic update status {0}")
    @ValueSource(ints = { 0, 1 })
    @DisplayName("#3299 Device list returns the actual toggle state under the autoUpdate contract")
    void serializedDeviceContainsAutoUpdateState(int autoUpdate) {
        DeviceEntity entity = new DeviceEntity();
        entity.setAutoUpdate(autoUpdate);
        DeviceServiceImpl deviceService = serviceReturning(entity);

        UserShowDeviceListVO device = deviceService.getUserDeviceList(1L, "agent-id").getFirst();
        ObjectMapper objectMapper = new WebMvcConfig().jackson2HttpMessageConverter().getObjectMapper();
        JsonNode payload = objectMapper.valueToTree(device);

        assertAll(
                () -> assertEquals(autoUpdate, device.getAutoUpdate()),
                () -> assertEquals(autoUpdate, payload.path("autoUpdate").asInt()),
                () -> assertTrue(payload.path("otaUpgrade").isMissingNode(),
                        "Device lists must not expose the unmapped legacy otaUpgrade field"));
    }

    private DeviceServiceImpl serviceReturning(DeviceEntity entity) {
        return new DeviceServiceImpl(null, null, null, null, null, null, null) {
            @Override
            public List<DeviceEntity> getUserDevices(Long userId, String agentId) {
                return List.of(entity);
            }
        };
    }
}
