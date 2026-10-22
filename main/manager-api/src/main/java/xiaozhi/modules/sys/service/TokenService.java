package xiaozhi.modules.sys.service;

public interface TokenService {
    /**
     * Generate a token
     *
     * @param userId
     * @return
     */
    String createToken(long userId);
}
