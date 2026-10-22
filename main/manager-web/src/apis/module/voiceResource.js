import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
    // Get paginated voice resources
    getVoiceResourceList(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get voice resources:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceList(params, callback);
                });
            }).send();
    },
    // Get a single voice resource
    getVoiceResourceInfo(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/${id}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get voice resource information:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceInfo(id, callback);
                });
            }).send();
    },
    // Save a voice resource
    saveVoiceResource(entity, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource`)
            .method('POST')
            .data(entity)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to save the voice resource:', err);
                RequestService.reAjaxFun(() => {
                    this.saveVoiceResource(entity, callback);
                });
            }).send();
    },
    // Delete a voice resource
    deleteVoiceResource(ids, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/${ids}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to delete the voice resource:', err);
                RequestService.reAjaxFun(() => {
                    this.deleteVoiceResource(ids, callback);
                });
            }).send();
    },
    // Get voice resources by user ID
    getVoiceResourceByUserId(userId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/user/${userId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get user voice resources:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceByUserId(userId, callback);
                });
            }).send();
    },
    // Get TTS platforms
    getTtsPlatformList(callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/ttsPlatforms`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get TTS platforms:', err);
                RequestService.reAjaxFun(() => {
                    this.getTtsPlatformList(callback);
                });
            }).send();
    }
}
