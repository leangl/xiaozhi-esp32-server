import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
    // Get dictionary types
    getDictTypeList(params, callback) {
        const queryParams = new URLSearchParams({
            dictType: params.dictType || '',
            dictName: params.dictName || '',
            page: params.page || 1,
            limit: params.limit || 10
        }).toString();

        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/type/page?${queryParams}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to get dictionary types:', err)
                this.$message.error(err.msg || '获取字典类型列表失败')
                RequestService.reAjaxFun(() => {
                    this.getDictTypeList(params, callback)
                })
            }).send()
    },

    // Get dictionary type details
    getDictTypeDetail(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/type/${id}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to get dictionary type details:', err)
                this.$message.error(err.msg || '获取字典类型详情失败')
                RequestService.reAjaxFun(() => {
                    this.getDictTypeDetail(id, callback)
                })
            }).send()
    },

    // Add a dictionary type
    addDictType(data, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/type/save`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to add the dictionary type:', err)
                this.$message.error(err.msg || '新增字典类型失败')
                RequestService.reAjaxFun(() => {
                    this.addDictType(data, callback)
                })
            }).send()
    },

    // Update a dictionary type
    updateDictType(data, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/type/update`)
            .method('PUT')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to update the dictionary type:', err)
                this.$message.error(err.msg || '更新字典类型失败')
                RequestService.reAjaxFun(() => {
                    this.updateDictType(data, callback)
                })
            }).send()
    },

    // Delete a dictionary type
    deleteDictType(ids, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/type/delete`)
            .method('POST')
            .data(ids)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to delete the dictionary type:', err)
                this.$message.error(err.msg || '删除字典类型失败')
                RequestService.reAjaxFun(() => {
                    this.deleteDictType(ids, callback)
                })
            }).send()
    },

    // Get dictionary entries
    getDictDataList(params, callback) {
        const queryParams = new URLSearchParams({
            dictTypeId: params.dictTypeId,
            dictLabel: params.dictLabel || '',
            dictValue: params.dictValue || '',
            page: params.page || 1,
            limit: params.limit || 10
        }).toString();

        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/data/page?${queryParams}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to get dictionary entries:', err)
                this.$message.error(err.msg || '获取字典数据列表失败')
                RequestService.reAjaxFun(() => {
                    this.getDictDataList(params, callback)
                })
            }).send()
    },

    // Get dictionary entry details
    getDictDataDetail(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/data/${id}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to get dictionary entry details:', err)
                this.$message.error(err.msg || '获取字典数据详情失败')
                RequestService.reAjaxFun(() => {
                    this.getDictDataDetail(id, callback)
                })
            }).send()
    },

    // Add a dictionary entry
    addDictData(data, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/data/save`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to add the dictionary entry:', err)
                this.$message.error(err.msg || '新增字典数据失败')
                RequestService.reAjaxFun(() => {
                    this.addDictData(data, callback)
                })
            }).send()
    },

    // Update a dictionary entry
    updateDictData(data, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/data/update`)
            .method('PUT')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to update the dictionary entry:', err)
                this.$message.error(err.msg || '更新字典数据失败')
                RequestService.reAjaxFun(() => {
                    this.updateDictData(data, callback)
                })
            }).send()
    },

    // Delete a dictionary entry
    deleteDictData(ids, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/admin/dict/data/delete`)
            .method('POST')
            .data(ids)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('Failed to delete the dictionary entry:', err)
                this.$message.error(err.msg || '删除字典数据失败')
                RequestService.reAjaxFun(() => {
                    this.deleteDictData(ids, callback)
                })
            }).send()
    },

    // Get dictionary entries
    getDictDataByType(dictType) {
        return new Promise((resolve, reject) => {
            RequestService.sendRequest()
                .url(`${getServiceUrl()}/admin/dict/data/type/${dictType}`)
                .method('GET')
                .success((res) => {
                    RequestService.clearRequestTime()
                    if (res.data && res.data.code === 0) {
                        resolve(res.data)
                    } else {
                        reject(new Error(res.data?.msg || '获取字典数据列表失败'))
                    }
                })
                .networkFail((err) => {
                    console.error('Failed to get dictionary entries:', err)
                    reject(err)
                }).send()
        })
    }

}
