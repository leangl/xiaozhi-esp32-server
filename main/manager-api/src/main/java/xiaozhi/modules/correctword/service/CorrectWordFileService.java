package xiaozhi.modules.correctword.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.correctword.dto.CorrectWordFileCreateDTO;
import xiaozhi.modules.correctword.vo.CorrectWordFileVO;
import xiaozhi.modules.correctword.vo.CorrectWordSimpleVO;

public interface CorrectWordFileService {

    /**
     * Create a replacement word file
     *
     * @param dto creation parameters
     * @return file VO
     */
    CorrectWordFileVO createFile(CorrectWordFileCreateDTO dto);

    /**
     * Update a replacement word file, replacing all entries
     *
     * @param fileId file ID
     * @param dto update parameters
     */
    void updateFile(String fileId, CorrectWordFileCreateDTO dto);

    /**
     * Get the current user's replacement word files
     *
     * @param params pagination parameters
     * @return paginated data
     */
    PageData<CorrectWordFileVO> listFiles(Map<String, Object> params);

    /**
     * Get the current user's replacement word files without pagination, for dropdown selection
     *
     * @return file list
     */
    List<CorrectWordFileVO> listAllFiles();

    /**
     * Get the original file content for downloading
     *
     * @param fileId file ID
     * @return file entity
     */
    CorrectWordFileVO getFileContent(String fileId);

    /**
     * Delete a replacement word file, its entries, and its associations
     *
     * @param fileId file ID
     */
    void deleteFile(String fileId);

    /**
     * Delete an agent's replacement word file associations without deleting the files
     *
     * @param agentId agent ID
     */
    void deleteMappingsByAgentId(String agentId);

    /**
     * Get all agent replacement word entries in compact device format
     *
     * @param agentId agent ID
     * @return replacement word list
     */
    List<CorrectWordSimpleVO> getAllItemsByAgentId(String agentId);

    /**
     * Get replacement word file IDs associated with an agent
     *
     * @param agentId agent ID
     * @return file ID list
     */
    List<String> getAgentCorrectWordFileIds(String agentId);

    /**
     * Replace all replacement word files associated with an agent
     *
     * @param agentId agent ID
     * @param fileIds list of file IDs
     */
    void saveAgentCorrectWords(String agentId, List<String> fileIds);

    /**
     * Batch delete replacement word files
     *
     * @param fileIds list of file IDs
     */
    void batchDeleteFiles(List<String> fileIds);
}
