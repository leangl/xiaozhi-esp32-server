package xiaozhi.modules.agent.service.impl;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.spring.repository.CrudRepository;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.ApprovedServicePolicy;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.AgentVoicePrintUpdateDTO;
import xiaozhi.modules.agent.dto.IdentifyVoicePrintResponse;
import xiaozhi.modules.agent.entity.AgentVoicePrintEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentVoicePrintService;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * @author zjy
 */
@Service
@Slf4j
public class AgentVoicePrintServiceImpl extends CrudRepository<AgentVoicePrintDao, AgentVoicePrintEntity>
        implements AgentVoicePrintService {
    private final AgentChatAudioService agentChatAudioService;
    private final RestTemplate restTemplate;
    private final SysParamsService sysParamsService;
    private final AgentChatHistoryService agentChatHistoryService;
    // Spring Boot programmatic transaction support
    private final TransactionTemplate transactionTemplate;
    // Recognition threshold
    private final Double RECOGNITION = 0.5;
    private final Executor taskExecutor;

    public AgentVoicePrintServiceImpl(AgentChatAudioService agentChatAudioService, RestTemplate restTemplate,
                                      SysParamsService sysParamsService, AgentChatHistoryService agentChatHistoryService,
                                      TransactionTemplate transactionTemplate, @Qualifier("taskExecutor") Executor taskExecutor) {
        this.agentChatAudioService = agentChatAudioService;
        this.restTemplate = restTemplate;
        this.sysParamsService = sysParamsService;
        this.agentChatHistoryService = agentChatHistoryService;
        this.transactionTemplate = transactionTemplate;
        this.taskExecutor = taskExecutor;
    }

    @Override
    public boolean insert(AgentVoicePrintSaveDTO dto) {
        getVoicePrintURI();
        // Get audio data
        ByteArrayResource resource = getVoicePrintAudioWAV(dto.getAgentId(), dto.getAudioId());
        // Check whether this voice is already registered
        IdentifyVoicePrintResponse response = identifyVoicePrint(dto.getAgentId(), resource);
        if (response != null && response.getScore() > RECOGNITION) {
            // Look up user information using the recognized voiceprint ID
            AgentVoicePrintEntity existingVoicePrint = baseMapper.selectById(response.getSpeakerId());
            // Preserve the localized "unknown user" fallback inserted into the existing user-facing error.
            String existingUserName = existingVoicePrint != null ? existingVoicePrint.getSourceName() : "未知用户";
            throw new RenException(ErrorCode.VOICEPRINT_ALREADY_REGISTERED, existingUserName);
        }
        AgentVoicePrintEntity entity = ConvertUtils.sourceToTarget(dto, AgentVoicePrintEntity.class);
        // Begin a transaction
        return Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                // Save voiceprint information
                int row = baseMapper.insert(entity);
                // If the insert affects other than one row, roll back the failed save
                if (row != 1) {
                    status.setRollbackOnly(); // Mark the transaction for rollback
                    return false;
                }
                // Send a voiceprint registration request
                registerVoicePrint(entity.getId(), resource);
                return true;
            } catch (RenException e) {
                status.setRollbackOnly(); // Mark the transaction for rollback
                throw e;
            } catch (Exception e) {
                status.setRollbackOnly(); // Mark the transaction for rollback
                log.error("Failed to save voiceprint");
                throw new RenException(ErrorCode.VOICE_PRINT_SAVE_ERROR);
            }
        }));
    }

    @Override
    public boolean delete(Long userId, String voicePrintId) {
        // Begin a transaction
        boolean b = Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                // Delete a voiceprint for the specified logged-in user and agent
                int row = baseMapper.delete(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .eq(AgentVoicePrintEntity::getId, voicePrintId)
                        .eq(AgentVoicePrintEntity::getCreator, userId));
                if (row != 1) {
                    status.setRollbackOnly(); // Mark the transaction for rollback
                    return false;
                }

                return true;
            } catch (Exception e) {
                status.setRollbackOnly(); // Mark the transaction for rollback
                log.error("Failed to delete voiceprint");
                throw new RenException(ErrorCode.VOICEPRINT_DELETE_ERROR);
            }
        }));
        // Delete from the voiceprint service only after successful database deletion
        if(b){
            taskExecutor.execute(()-> {
                try {
                    cancelVoicePrint(voicePrintId);
                }catch (RuntimeException e) {
                    log.error("Voiceprint service cleanup unavailable");
                }
            });
        }
        return b;
    }

    @Override
    public List<AgentVoicePrintVO> list(Long userId, String agentId) {
        // Find records for the specified logged-in user and agent
        List<AgentVoicePrintEntity> list = baseMapper.selectList(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                .eq(AgentVoicePrintEntity::getAgentId, agentId)
                .eq(AgentVoicePrintEntity::getCreator, userId));
        return list.stream().map(entity -> {
            // Convert entries to AgentVoicePrintVO
            return ConvertUtils.sourceToTarget(entity, AgentVoicePrintVO.class);
        }).toList();

    }

    @Override
    public boolean update(Long userId, AgentVoicePrintUpdateDTO dto) {
        AgentVoicePrintEntity agentVoicePrintEntity = baseMapper
                .selectOne(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .eq(AgentVoicePrintEntity::getId, dto.getId())
                        .eq(AgentVoicePrintEntity::getCreator, userId));
        if (agentVoicePrintEntity == null) {
            return false;
        }
        // Get the audio ID
        String audioId = dto.getAudioId();
        // Get the agent ID
        String agentId = agentVoicePrintEntity.getAgentId();
        ByteArrayResource resource;
        // If audioId is nonempty and differs from the stored ID, reload audio and regenerate the voiceprint
        if (!StringUtils.isEmpty(audioId) && !audioId.equals(agentVoicePrintEntity.getAudioId())) {
            getVoicePrintURI();
            resource = getVoicePrintAudioWAV(agentId, audioId);

            // Check whether this voice is already registered
            IdentifyVoicePrintResponse response = identifyVoicePrint(agentId, resource);
            // A score above RECOGNITION means the voiceprint already exists
            if (response != null && response.getScore() > RECOGNITION) {
                // If the returned ID differs from the voiceprint being updated, this voice belongs to another voiceprint; reject the update
                if (!response.getSpeakerId().equals(dto.getId())) {
                    // Look up user information using the recognized voiceprint ID
                    AgentVoicePrintEntity existingVoicePrint = baseMapper.selectById(response.getSpeakerId());
                    // Preserve the localized "unknown user" fallback inserted into the existing user-facing error.
                    String existingUserName = existingVoicePrint != null ? existingVoicePrint.getSourceName() : "未知用户";
                    throw new RenException(ErrorCode.VOICEPRINT_UPDATE_NOT_ALLOWED, existingUserName);
                }
            }
        } else {
            resource = null;
        }
        // Begin a transaction
        return Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                AgentVoicePrintEntity entity = ConvertUtils.sourceToTarget(dto, AgentVoicePrintEntity.class);
                int row = baseMapper.updateById(entity);
                if (row != 1) {
                    status.setRollbackOnly(); // Mark the transaction for rollback
                    return false;
                }
                if (resource != null) {
                    String id = entity.getId();
                    // Deregister the existing vector for this voiceprint ID first
                    cancelVoicePrint(id);
                    // Send a voiceprint registration request
                    registerVoicePrint(id, resource);
                }
                return true;
            } catch (RenException e) {
                status.setRollbackOnly(); // Mark the transaction for rollback
                throw e;
            } catch (Exception e) {
                status.setRollbackOnly(); // Mark the transaction for rollback
                log.error("Failed to update voiceprint");
                throw new RenException(ErrorCode.VOICEPRINT_UPDATE_ADMIN_ERROR);
            }
        }));
    }

    /**
     * Get the voiceprint API URI
     *
     * @return URI object
     */
    private URI getVoicePrintURI() {
        // Get the voiceprint API URL
        String voicePrint = sysParamsService.getValue(Constant.SERVER_VOICE_PRINT, true);
        try {
            URI uri = ApprovedServicePolicy.validateEndpoint(voicePrint, "voiceprint");
            getAuthorization(uri);
            return uri;
        } catch (RuntimeException e) {
            throw new RenException(ErrorCode.VOICEPRINT_API_URI_ERROR);
        }
    }

    /**
     * Get the voiceprint URL base path
     * 
     * @param uri voiceprint URI
     * @return base path
     */
    private String getBaseUrl(URI uri) {
        return uri.resolve("/").toString().replaceAll("/$", "");
    }

    /**
     * Get the Authorization credential
     *
     * @param uri voiceprint URI
     * @return Authorization value
     */
    private String getAuthorization(URI uri) {
        // Get parameters
        String query = uri.getRawQuery();
        if (query == null) throw new RenException(ErrorCode.VOICEPRINT_API_URI_ERROR);
        List<String> keys = Arrays.stream(query.split("&"))
                .filter(pair -> pair.startsWith("key=")).map(pair -> pair.substring(4)).toList();
        if (keys.size() != 1 || keys.getFirst().isBlank()) {
            throw new RenException(ErrorCode.VOICEPRINT_API_URI_ERROR);
        }
        return "Bearer " + URLDecoder.decode(keys.getFirst().replace("+", "%2B"), StandardCharsets.UTF_8);
    }

    /**
     * Get voiceprint audio resource data
     *
     * @param audioId audio ID
     * @return voiceprint audio resource data
     */
    private ByteArrayResource getVoicePrintAudioWAV(String agentId, String audioId) {
        // Check whether this audio belongs to the current agent
        boolean b = agentChatHistoryService.isAudioOwnedByAgent(audioId, agentId);
        if (!b) {
            throw new RenException(ErrorCode.VOICEPRINT_AUDIO_NOT_BELONG_AGENT);
        }
        // Get audio data
        byte[] audio = agentChatAudioService.getAudio(audioId);
        // Fail immediately if audio data is empty
        if (audio == null || audio.length == 0) {
            throw new RenException(ErrorCode.VOICEPRINT_AUDIO_EMPTY);
        }
        // Wrap the byte array as a resource and return it
        return new ByteArrayResource(audio) {
            @Override
            public String getFilename() {
                return "VoicePrint.WAV"; // Set the file name
            }
        };
    }

    /**
     * Send a voiceprint registration HTTP request
     * 
     * @param id voiceprint ID
     * @param resource voiceprint audio resource
     */
    private void registerVoicePrint(String id, ByteArrayResource resource) {
        // Extract the voiceprint API URL prefix
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/register";
        // Create the request body
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("speaker_id", id);
        body.add("file", resource);

        // Create request headers
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        // Create the request body
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        // Send a POST request
        ResponseEntity<String> response = exchangeVoicePrint(requestUrl, HttpMethod.POST, requestEntity,
                ErrorCode.VOICEPRINT_REGISTER_REQUEST_ERROR);

        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voiceprint registration failed");
            throw new RenException(ErrorCode.VOICEPRINT_REGISTER_REQUEST_ERROR);
        }
        // Check response content
        String responseBody = response.getBody();
        if (responseBody == null || !responseBody.contains("true")) {
            log.error("Voiceprint registration returned an unsuccessful result");
            throw new RenException(ErrorCode.VOICEPRINT_REGISTER_PROCESS_ERROR);
        }
    }

    /**
     * Send a voiceprint deregistration request
     * 
     * @param voicePrintId voiceprint ID
     */
    private void cancelVoicePrint(String voicePrintId) {
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/" + voicePrintId;
        // Create request headers
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        // Create the request body
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(headers);

        // Send a POST request
        ResponseEntity<String> response = exchangeVoicePrint(requestUrl, HttpMethod.DELETE, requestEntity,
                ErrorCode.VOICEPRINT_UNREGISTER_REQUEST_ERROR);
        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voiceprint deregistration failed");
            throw new RenException(ErrorCode.VOICEPRINT_UNREGISTER_REQUEST_ERROR);
        }
        // Check response content
        String responseBody = response.getBody();
        if (responseBody == null || !responseBody.contains("true")) {
            log.error("Voiceprint deregistration returned an unsuccessful result");
            throw new RenException(ErrorCode.VOICEPRINT_UNREGISTER_PROCESS_ERROR);
        }
    }

    /**
     * Send a voiceprint recognition HTTP request
     * 
     * @param agentId agent ID
     * @param resource voiceprint audio resource
     * @return recognition data
     */
    private IdentifyVoicePrintResponse identifyVoicePrint(String agentId, ByteArrayResource resource) {

        // Get all registered voiceprints for this agent
        List<AgentVoicePrintEntity> agentVoicePrintList = baseMapper
                .selectList(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .select(AgentVoicePrintEntity::getId)
                        .eq(AgentVoicePrintEntity::getAgentId, agentId));

        // Skip recognition if no voiceprints are registered
        if (agentVoicePrintList.isEmpty()) {
            return null;
        }
        // Extract the voiceprint API URL prefix
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/identify";
        // Create the request body
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        // Create the speaker_id parameter
        String speakerIds = agentVoicePrintList.stream()
                .map(AgentVoicePrintEntity::getId)
                .collect(Collectors.joining(","));
        body.add("speaker_ids", speakerIds);
        body.add("file", resource);

        // Create request headers
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        // Create the request body
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        // Send a POST request
        ResponseEntity<String> response = exchangeVoicePrint(requestUrl, HttpMethod.POST, requestEntity,
                ErrorCode.VOICEPRINT_IDENTIFY_REQUEST_ERROR);

        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voiceprint recognition request failed");
            throw new RenException(ErrorCode.VOICEPRINT_IDENTIFY_REQUEST_ERROR);
        }
        // Check response content
        String responseBody = response.getBody();
        if (responseBody != null) {
            try {
                return JsonUtils.parseObject(responseBody, IdentifyVoicePrintResponse.class);
            } catch (RuntimeException e) {
                throw new RenException(ErrorCode.VOICEPRINT_IDENTIFY_REQUEST_ERROR);
            }
        }
        return null;
    }

    private ResponseEntity<String> exchangeVoicePrint(String url, HttpMethod method, HttpEntity<?> request, int error) {
        try {
            ApprovedServicePolicy.validateEndpoint(url, "voiceprint");
            return restTemplate.exchange(URI.create(url), method, request, String.class);
        } catch (RuntimeException e) {
            throw new RenException(error);
        }
    }
}
