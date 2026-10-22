import { Message } from 'element-ui'
import router from '../router'
import Constant from '../utils/constant'

/**
 * Check whether the user is logged in
 */
export function checkUserLogin(fn) {
    let token = localStorage.getItem(Constant.STORAGE_KEY.TOKEN)
    let userType = localStorage.getItem(Constant.STORAGE_KEY.USER_TYPE)
    if (isNull(token) || isNull(userType)) {
        goToPage('console', true)
        return
    }
    if (fn) {
        fn()
    }
}

/**
 * Check for an empty value
 * @param data
 * @returns {boolean}
 */
export function isNull(data) {
    if (data === undefined) {
        return true
    } else if (data === null) {
        return true
    } else if (typeof data === 'string' && (data.length === 0 || data === '' || data === 'undefined' || data === 'null')) {
        return true
    } else if ((data instanceof Array) && data.length === 0) {
        return true
    }
    return false
}

/**
 * Check for a nonempty value
 * @param data
 * @returns {boolean}
 */
export function isNotNull(data) {
    return !isNull(data)
}

/**
 * Show a red notification at the top
 * @param msg
 */
export function showDanger(msg) {
    if (isNull(msg)) {
        return
    }
    Message({
        message: msg,
        type: 'error',
        showClose: true
    })
}

/**
 * Show an orange notification at the top
 * @param msg
 */
export function showWarning(msg) {
    if (isNull(msg)) {
        return
    }
    Message({
        message: msg,
        type: 'warning',
        showClose: true
    });
}



/**
 * Show a green notification at the top
 * @param msg
 */
export function showSuccess(msg) {
    Message({
        message: msg,
        type: 'success',
        showClose: true
    })
}



/**
 * Navigate to a page
 * @param path
 * @param isRepalce
 */
export function goToPage(path, isRepalce) {
    if (isRepalce) {
        router.replace(path)
    } else {
        router.push(path)
    }
}

/**
 * Get the current Vue page name
 * @param path
 * @param isRepalce
 */
export function getCurrentPage() {
    let hash = location.hash.replace('#', '')
    if (hash.indexOf('?') > 0) {
        hash = hash.substring(0, hash.indexOf('?'))
    }
    return hash
}

/**
 * Generate a random number in [min,max]
 * @param min
 * @param max
 * @returns {number}
 */
export function randomNum(min, max) {
    return Math.round(Math.random() * (max - min) + min)
}


/**
 * Get a UUID
 */
export function getUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        return (c === 'x' ? (Math.random() * 16 | 0) : ('r&0x3' | '0x8')).toString(16)
    })
}


/**
 * Validate mobile-number format
 * @param {string} mobile Mobile number
 * @param {string} areaCode Calling code
 * @returns {boolean}
 */
export function validateMobile(mobile, areaCode) {
    // Remove nondigit characters
    const cleanMobile = mobile.replace(/\D/g, '');

    // Use the validation rule for the calling code
    switch (areaCode) {
        case '+86': // Mainland China
            return /^1[3-9]\d{9}$/.test(cleanMobile);
        case '+852': // Hong Kong, China
            return /^[569]\d{7}$/.test(cleanMobile);
        case '+853': // Macao, China
            return /^6\d{7}$/.test(cleanMobile);
        case '+886': // Taiwan, China
            return /^9\d{8}$/.test(cleanMobile);
        case '+1': // United States / Canada
            return /^[2-9]\d{9}$/.test(cleanMobile);
        case '+44': // United Kingdom
            return /^7[1-9]\d{8}$/.test(cleanMobile);
        case '+81': // Japan
            return /^[7890]\d{8}$/.test(cleanMobile);
        case '+82': // South Korea
            return /^1[0-9]\d{7}$/.test(cleanMobile);
        case '+65': // Singapore
            return /^[89]\d{7}$/.test(cleanMobile);
        case '+61': // Australia
            return /^[4578]\d{8}$/.test(cleanMobile);
        case '+49': // Germany
            return /^1[5-7]\d{8}$/.test(cleanMobile);
        case '+33': // France
            return /^[67]\d{8}$/.test(cleanMobile);
        case '+39': // Italy
            return /^3[0-9]\d{8}$/.test(cleanMobile);
        case '+34': // Spain
            return /^[6-9]\d{8}$/.test(cleanMobile);
        case '+55': // Brazil
            return /^[1-9]\d{10}$/.test(cleanMobile);
        case '+91': // India
            return /^[6-9]\d{9}$/.test(cleanMobile);
        case '+971': // United Arab Emirates
            return /^[5]\d{8}$/.test(cleanMobile);
        case '+966': // Saudi Arabia
            return /^[5]\d{8}$/.test(cleanMobile);
        case '+880': // Bangladesh
            return /^1[3-9]\d{8}$/.test(cleanMobile);
        case '+234': // Nigeria
            return /^[789]\d{9}$/.test(cleanMobile);
        case '+254': // Kenya
            return /^[17]\d{8}$/.test(cleanMobile);
        case '+255': // Tanzania
            return /^[67]\d{8}$/.test(cleanMobile);
        case '+7': // Kazakhstan
            return /^[67]\d{9}$/.test(cleanMobile);
        default:
            // Other international numbers: 5 to 15 digits
            return /^\d{5,15}$/.test(cleanMobile);
    }
}


/**
 * Generate an SM2 key pair in hexadecimal format
 * @returns {Object} Object containing the public and private keys
 */
export function generateSm2KeyPairHex() {
    // Generate an SM2 key pair with sm-crypto
    const sm2 = require('sm-crypto').sm2;
    const keypair = sm2.generateKeyPairHex();
    
    return {
        publicKey: keypair.publicKey,
        privateKey: keypair.privateKey,
        clientPublicKey: keypair.publicKey, // Client public key
        clientPrivateKey: keypair.privateKey // Client private key
    };
}

/**
 * Encrypt using an SM2 public key
 * @param {string} publicKey Public key in hexadecimal format
 * @param {string} plainText Plaintext
 * @returns {string} Ciphertext in hexadecimal format
 */
export function sm2Encrypt(publicKey, plainText) {
    if (!publicKey) {
        throw new Error('Public key must not be null or undefined');
    }
    
    if (!plainText) {
        throw new Error('Plaintext must not be empty');
    }
    
    const sm2 = require('sm-crypto').sm2;
    // SM2 encryption: add the 04 prefix for an uncompressed public key
    const encrypted = sm2.doEncrypt(plainText, publicKey, 1);
    // Convert to hexadecimal with the 04 prefix to match the backend
    const result = "04" + encrypted;
    
    return result;
}

/**
 * Decrypt using an SM2 private key
 * @param {string} privateKey Private key in hexadecimal format
 * @param {string} cipherText Ciphertext in hexadecimal format
 * @returns {string} Decrypted plaintext
 */
export function sm2Decrypt(privateKey, cipherText) {
    const sm2 = require('sm-crypto').sm2;
    // Remove the 04 prefix to match the backend
    const dataWithoutPrefix = cipherText.startsWith("04") ? cipherText.substring(2) : cipherText;
    // SM2 decryption
    return sm2.doDecrypt(dataWithoutPrefix, privateKey, 1);
}

/**
 * Debounce function
 * @param {Function} fn Function to debounce
 * @param {number} delay Delay in milliseconds, default 500ms
 * @param {boolean} immediate Whether to execute immediately, default false
 * @returns {Function} Debounced function
 */
export function debounce(fn, delay = 500, immediate = false) {
    let timer = null;
    
    return function (...args) {
        const context = this;
        
        if (timer) {
            clearTimeout(timer);
        }
        
        if (immediate && !timer) {
            fn.apply(context, args);
        }
        
        timer = setTimeout(() => {
            if (!immediate) {
                fn.apply(context, args);
            }
            timer = null;
        }, delay);
    };
}

