package xiaozhi.modules.device.service.impl;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.device.dao.DeviceDao;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.security.user.SecurityUser;

@ExtendWith(MockitoExtension.class)
class DeviceBindingAuthorizationTest {
    private static final Long OWNER = 11L;
    private static final String AGENT = "synthetic-agent";
    private static final String MAC = "02:00:00:00:00:11";
    private static final String CODE = "123456";

    @Mock private DeviceDao devices;
    @Mock private AgentDao agents;
    @Mock private RedisUtils redis;
    @InjectMocks private DeviceServiceImpl service;
    private MockedStatic<SecurityUser> security;
    private MockedStatic<MessageUtils> messages;

    @BeforeEach
    void setup() {
        ReflectionTestUtils.setField(service, "baseDao", devices);
        security = mockStatic(SecurityUser.class);
        messages = mockStatic(MessageUtils.class);
        messages.when(() -> MessageUtils.getMessage(anyInt())).thenReturn("Synthetic error");
    }

    @AfterEach
    void closeStatics() {
        messages.close();
        security.close();
    }

    static Stream<Arguments> forbiddenAgents() {
        return Stream.of(
                Arguments.of(AGENT, 22L, false),
                Arguments.of(AGENT, null, false),
                Arguments.of(AGENT, null, true),
                Arguments.of(" ", null, true),
                Arguments.of(null, null, true));
    }

    @ParameterizedTest
    @MethodSource("forbiddenAgents")
    void activationRejectsBeforeDeviceOrActivationCacheAccess(String agentId, Long owner, boolean missing) {
        currentUser(OWNER);
        stubAgent(agentId, owner, missing);
        RenException error = assertThrows(RenException.class, () -> service.deviceActivation(agentId, CODE));
        assertEquals(ErrorCode.NO_PERMISSION, error.getCode());
        verifyNoInteractions(devices, redis);
    }

    @ParameterizedTest
    @MethodSource("forbiddenAgents")
    void manualBindingRejectsBeforeDeviceLookupOrCacheMutation(String agentId, Long owner, boolean missing) {
        stubAgent(agentId, owner, missing);
        RenException error = assertThrows(RenException.class, () -> service.manualAddDevice(OWNER, dto(agentId)));
        assertEquals(ErrorCode.NO_PERMISSION, error.getCode());
        verifyNoInteractions(devices, redis);
    }

    @Test
    void absentUserCannotUseEitherBindingRoute() {
        security.when(SecurityUser::getUser).thenReturn(new UserDetail());
        assertEquals(ErrorCode.USER_NOT_LOGIN,
                assertThrows(RenException.class, () -> service.deviceActivation(AGENT, CODE)).getCode());
        assertEquals(ErrorCode.USER_NOT_LOGIN,
                assertThrows(RenException.class, () -> service.manualAddDevice(null, dto(AGENT))).getCode());
        verifyNoInteractions(agents, devices, redis);
    }

    @Test
    void activationPreservesEmptyCodeError() {
        assertEquals(ErrorCode.ACTIVATION_CODE_EMPTY,
                assertThrows(RenException.class, () -> service.deviceActivation(AGENT, " ")).getCode());
        verifyNoInteractions(agents, devices, redis);
    }

    @Test
    void ownerCanManuallyBindWithExistingFieldsAndCacheInvalidation() {
        stubAgent(AGENT, OWNER, false);
        service.manualAddDevice(OWNER, dto(AGENT));
        assertOwnedInsert();
        verify(redis).delete(RedisKeys.getAgentDeviceCountById(AGENT));
    }

    @Test
    void ownerCanActivateAndConsumeOnlyTheSuccessfulCode() {
        currentUser(OWNER);
        stubAgent(AGENT, OWNER, false);
        String codeKey = RedisKeys.getOtaActivationCode(CODE);
        String infoKey = RedisKeys.getOtaDeviceActivationInfo(MAC.replace(":", "_"));
        when(redis.get(codeKey)).thenReturn(MAC);
        when(redis.get(infoKey)).thenReturn(Map.of("activation_code", CODE, "mac_address", MAC,
                "board", "synthetic-board", "app_version", "1.0.0"));
        assertTrue(service.deviceActivation(AGENT, CODE));
        assertOwnedInsert();
        verify(redis).delete(List.of(infoKey, codeKey, RedisKeys.getAgentDeviceCountById(AGENT)));
    }

    private void currentUser(Long id) {
        UserDetail user = new UserDetail();
        user.setId(id);
        security.when(SecurityUser::getUser).thenReturn(user);
    }

    private void stubAgent(String id, Long owner, boolean missing) {
        if (id == null || id.isBlank()) return;
        AgentEntity agent = new AgentEntity();
        agent.setId(id);
        agent.setUserId(owner);
        lenient().when(agents.selectById(id)).thenReturn(missing ? null : agent);
    }

    private DeviceManualAddDTO dto(String agentId) {
        DeviceManualAddDTO dto = new DeviceManualAddDTO();
        dto.setAgentId(agentId);
        dto.setMacAddress(MAC);
        dto.setBoard("synthetic-board");
        dto.setAppVersion("1.0.0");
        return dto;
    }

    private void assertOwnedInsert() {
        ArgumentCaptor<DeviceEntity> inserted = ArgumentCaptor.forClass(DeviceEntity.class);
        verify(devices).insert(inserted.capture());
        DeviceEntity entity = inserted.getValue();
        assertEquals(MAC, entity.getId());
        assertEquals(MAC, entity.getMacAddress());
        assertEquals(AGENT, entity.getAgentId());
        assertEquals(OWNER, entity.getUserId());
        assertEquals(OWNER, entity.getCreator());
        assertEquals(OWNER, entity.getUpdater());
        assertEquals("synthetic-board", entity.getBoard());
        assertEquals("1.0.0", entity.getAppVersion());
        assertEquals(1, entity.getAutoUpdate());
    }
}
