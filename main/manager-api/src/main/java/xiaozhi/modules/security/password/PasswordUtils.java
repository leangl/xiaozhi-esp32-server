package xiaozhi.modules.security.password;

/**
 * Password utilities
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
public class PasswordUtils {
    private static PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    /**
     * Encrypt
     *
     * @param str string
     * @return encrypted string
     */
    public static String encode(String str) {
        return passwordEncoder.encode(str);
    }

    /**
     * Compare passwords
     *
     * @param str plaintext password
     * @param password encrypted password
     * @return true on success, false on failure
     */
    public static boolean matches(String str, String password) {
        return passwordEncoder.matches(str, password);
    }

    public static void main(String[] args) {
        String str = "admin";
        String password = encode(str);

        System.out.println(password);
        System.out.println(matches(str, password));
    }

}
