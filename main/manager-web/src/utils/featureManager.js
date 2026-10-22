// Feature configuration utility
import Api from "@/apis/api";
import store from "@/store";

class FeatureManager {
    constructor() {
        this.defaultFeatures = {
            voiceprintRecognition: {
                name: 'feature.voiceprintRecognition.name',
                enabled: false,
                description: 'feature.voiceprintRecognition.description'
            },
            voiceClone: {
                name: 'feature.voiceClone.name',
                enabled: false,
                description: 'feature.voiceClone.description'
            },
            knowledgeBase: {
                name: 'feature.knowledgeBase.name',
                enabled: false,
                description: 'feature.knowledgeBase.description'
            },
            mcpAccessPoint: {
                name: 'feature.mcpAccessPoint.name',
                enabled: false,
                description: 'feature.mcpAccessPoint.description'
            },
            vad: {
                name: 'feature.vad.name',
                enabled: false,
                description: 'feature.vad.description'
            },
            asr: {
                name: 'feature.asr.name',
                enabled: false,
                description: 'feature.asr.description'
            },
            addressBook: {
                name: 'feature.addressBook.name',
                enabled: false,
                description: 'feature.addressBook.description'
            }
        };
        this.currentFeatures = { ...this.defaultFeatures }; // Current in-memory configuration
        this.initialized = false;
        this.initPromise = null;
    }

    /**
     * Wait for initialization
     */
    async waitForInitialization() {
        if (!this.initPromise) {
            this.initPromise = this.init();
        }
        await this.initPromise;
        return this.initialized;
    }

    /**
     * Initialize feature configuration
     */
    async init() {
        try {
            // Get configuration from the pub-config API
            const config = await this.getConfigFromPubConfig();
            if (config) {
                this.currentFeatures = { ...config }; // Store in memory
                this.initialized = true;
                return;
            }
        } catch (error) {
            console.warn('Failed to get configuration from the pub-config API:', error);
        }

        // Use default configuration if the pub-config API fails
        this.currentFeatures = { ...this.defaultFeatures }; // Store default configuration in memory
        this.initialized = true;
    }

    /**
     * Update the config cache
     */
    updateConfigCache(config) {
        store.commit('setPubConfig', config);
        localStorage.setItem('pubConfig', JSON.stringify(config));
    }

    /**
     * Get configuration from the pub-config API
     */
    async getConfigFromPubConfig() {
        return new Promise((resolve) => {
            // Call the pub-config API directly
            Api.user.getPubConfig((result) => {
                // Check the response structure
                if (result && result.status === 200) {
                    // Check for a data field
                    if (result.data) {
                        const configCache = result.data.data || {};
                        // Use the code field to determine success when present
                        if (result.data.code !== undefined) {
                            if (result.data.code === 0 && result.data.data && result.data.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.data.systemWebMenu === 'string') {
                                        // Parse JSON when the value is a string
                                        config = JSON.parse(result.data.data.systemWebMenu);
                                    } else {
                                        // Use object values directly
                                        config = result.data.data.systemWebMenu;
                                    }

                                    // Check for a features object in the configuration
                                    if (config && config.features) {
                                        // Ensure the knowledgeBase feature exists and is configured
                                        if (!config.features.knowledgeBase) {
                                            console.warn('Configuration lacks the knowledgeBase feature; merging defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('Configuration lacks the features object; using defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('The API code is nonzero or required data is missing; using defaults');
                                resolve(null);
                            }
                        } else {
                            // Check systemWebMenu directly when there is no code field
                            if (result.data && result.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.systemWebMenu === 'string') {
                                        // Parse JSON when the value is a string
                                        config = JSON.parse(result.data.systemWebMenu);
                                    } else {
                                        // Use object values directly
                                        config = result.data.systemWebMenu;
                                    }

                                    // Check for a features object in the configuration
                                    if (config && config.features) {
                                        // Ensure the knowledgeBase feature exists and is configured
                                        if (!config.features.knowledgeBase) {
                                            console.warn('Configuration lacks the knowledgeBase feature; merging defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('Configuration lacks the features object; using defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('The API response lacks systemWebMenu data; using defaults');
                                resolve(null);
                            }
                        }
                        this.updateConfigCache(configCache)
                    } else {
                        console.warn('The API response lacks a data field; using defaults');
                        resolve(null);
                    }
                } else {
                    console.warn('The pub-config API call failed; using defaults');
                    resolve(null);
                }
            });
        });
    }

    /**
     * Get the current configuration
     */
    getCurrentConfig() {
        // Return the current in-memory configuration
        return this.currentFeatures;
    }

    /**
     * Save configuration to the backend API
     */
    async saveConfig(config) {
        try {
            // Update in-memory configuration
            this.currentFeatures = { ...config };

            // Save to the backend API asynchronously
            this.saveConfigToAPI(config).catch(error => {
                console.warn('Failed to save configuration to the API:', error);
            }).finally(() => {
                this.init()
            });

            // Emit a configuration-change event
            window.dispatchEvent(new CustomEvent('featureConfigChanged', {
                detail: config
            }));
        } catch (error) {
            console.error('Failed to save feature configuration:', error);
        }
    }

    /**
     * Save configuration to the backend API
     */
    async saveConfigToAPI(config) {
        return new Promise((resolve) => {
            // Update the parameter using the known ID (600)
            Api.admin.updateParam(
                {
                    id: 600,
                    paramCode: 'system-web.menu',
                    paramValue: JSON.stringify({
                        features: config,
                        groups: {
                            featureManagement: ["voiceprintRecognition", "voiceClone", "knowledgeBase", "mcpAccessPoint", "addressBook"],
                            voiceManagement: ["vad", "asr"]
                        }
                    }),
                    valueType: 'json',
                    // Preserve persisted parameter metadata sent to the backend.
                    remark: '系统功能菜单配置'
                },
                (updateResult) => {
                    if (updateResult.code === 0) {
                        resolve();
                    } else {
                        // Log update failures without blocking the localStorage save
                        console.warn('Failed to update the parameter:', updateResult.msg);
                        resolve(); // Do not block the localStorage save
                    }
                },
                (error) => {
                    console.warn('Failed to update the parameter:', error);
                    resolve(); // Do not block the localStorage save
                }
            );
        });
    }



    /**
     * Get all feature configurations
     */
    getAllFeatures() {
        return this.getCurrentConfig();
    }

    /**
     * Get a simplified configuration object for the home component
     */
    getConfig() {
        const features = this.getAllFeatures();
        return {
            voiceprintRecognition: features.voiceprintRecognition?.enabled || false,
            voiceClone: features.voiceClone?.enabled || false,
            knowledgeBase: features.knowledgeBase?.enabled || false,
            mcpAccessPoint: features.mcpAccessPoint?.enabled || false,
            vad: features.vad?.enabled || false,
            asr: features.asr?.enabled || false,
            addressBook: features.addressBook?.enabled || false
        };
    }

    /**
     * Get the state of a specified feature
     */
    getFeatureStatus(featureKey) {
        const features = this.getAllFeatures();
        return features[featureKey]?.enabled || false;
    }

    /**
     * Set feature state
     */
    setFeatureStatus(featureKey, enabled) {
        const features = this.getAllFeatures();
        if (features[featureKey]) {
            features[featureKey].enabled = enabled;
            this.saveConfig(features);
            return true;
        }
        return false;
    }

    /**
     * Enable a feature
     */
    enableFeature(featureKey) {
        return this.setFeatureStatus(featureKey, true);
    }

    /**
     * Disable a feature
     */
    disableFeature(featureKey) {
        return this.setFeatureStatus(featureKey, false);
    }

    /**
     * Toggle feature state
     */
    toggleFeature(featureKey) {
        const currentStatus = this.getFeatureStatus(featureKey);
        return this.setFeatureStatus(featureKey, !currentStatus);
    }

    /**
     * Reset all features to defaults
     */
    resetToDefault() {
        this.saveConfig(this.defaultFeatures);
    }

    /**
     * Batch-update feature states
     */
    updateFeatures(featureUpdates) {
        const features = this.getAllFeatures();
        Object.keys(featureUpdates).forEach(featureKey => {
            if (features[featureKey]) {
                features[featureKey].enabled = featureUpdates[featureKey];
            } else if (this.defaultFeatures[featureKey]) {
                features[featureKey] = { ...this.defaultFeatures[featureKey] };
                features[featureKey].enabled = featureUpdates[featureKey];
            }
        });
        this.saveConfig(features);
    }

    /**
     * Get enabled features
     */
    getEnabledFeatures() {
        const features = this.getAllFeatures();
        return Object.keys(features).filter(key => features[key].enabled);
    }

    /**
     * Check whether a feature is enabled
     */
    isFeatureEnabled(featureKey) {
        return this.getFeatureStatus(featureKey);
    }
}

// Create the singleton instance
const featureManager = new FeatureManager();

export default featureManager;
