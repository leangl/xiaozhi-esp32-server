package xiaozhi.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

// Chinese plaintext samples exercise UTF-8 encryption/decryption and Python interoperability; preserve fixture bytes.
public class AESUtilsTest {

    @Test
    public void testEncryptAndDecrypt() {
        String key = "xiaozhi1234567890";
        String plainText = "Hello, 小智!";

        System.out.println("Original text: " + plainText);
        System.out.println("Key: " + key);

        // Encrypt
        String encrypted = AESUtils.encrypt(key, plainText);
        System.out.println("Encrypted result: " + encrypted);

        // Decrypt
        String decrypted = AESUtils.decrypt(key, encrypted);
        System.out.println("Decrypted result: " + decrypted);

        // Verify
        assertEquals(plainText, decrypted, "Encryption and decryption results should match");
        System.out.println("Encryption/decryption consistency: " + plainText.equals(decrypted));
    }

    @Test
    public void testDifferentKeyLengths() {
        String[] keys = {
                "1234567890123456", // 16 bytes
                "123456789012345678901234", // 24 bytes
                "12345678901234567890123456789012", // 32 bytes
                "short", // Short key
                "verylongkeythatwillbetruncatedto32bytes" // Long key
        };

        String plainText = "测试文本";

        for (String key : keys) {
            String encrypted = AESUtils.encrypt(key, plainText);
            String decrypted = AESUtils.decrypt(key, encrypted);
            assertEquals(plainText, decrypted, "Key length: " + key.length());
        }
    }

    @Test
    public void testSpecialCharacters() {
        String key = "xiaozhi1234567890";
        String[] testTexts = {
                "Hello World",
                "你好世界",
                "Hello, 小智!",
                "特殊字符: !@#$%^&*()",
                "数字123和中文混合",
                "Emoji: 😀🎉🚀",
                "空字符串测试",
                ""
        };

        for (String text : testTexts) {
            String encrypted = AESUtils.encrypt(key, text);
            String decrypted = AESUtils.decrypt(key, encrypted);
            assertEquals(text, decrypted, "Test text: " + text);
        }
    }

    @Test
    public void testCrossLanguageCompatibility() {
        // Python-generated ciphertext for cross-language compatibility testing
        String key = "xiaozhi1234567890";
        String plainText = "Hello, 小智!";

        // Python-generated ciphertext (obtain by running the Python tests)
        // String pythonEncrypted = "ciphertext from the Python test";
        // String decrypted = AESUtils.decrypt(key, pythonEncrypted);
        // assertEquals(plainText, decrypted, "Java should decrypt Python-generated ciphertext");

        // Generate Java ciphertext for Python testing
        String javaEncrypted = AESUtils.encrypt(key, plainText);
        System.out.println("Java ciphertext for Python testing: " + javaEncrypted);
    }
}
