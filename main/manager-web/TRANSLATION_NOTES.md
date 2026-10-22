# Web translation exceptions

This note covers only `main/manager-web`. It records exact retained regions for the parent translation inventory. Line numbers describe this translation slice; match the quoted source or dictionary key if later edits move a line.

The code examples below use JSON string notation with Unicode escapes for Han characters. Decoding the escapes gives the exact source line. They are documentation of existing data, not replacement values or instructions to execute.

## Source regions

The source scan found 80 remaining Han-bearing lines outside the two protected Chinese dictionaries. This table gives a reason for each line; it does not exempt entire source directories.

| Source location | Exact retained source line (JSON notation) | Category and reason |
| --- | --- | --- |
| `src/apis/httpRequest.js:144` | <code>"showDanger(&#96;\u7f51\u7edc\u8bf7\u6c42\u51fa\u73b0\u4e86\u9519\u8bef【${info.status}】&#96;)"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/httpRequest.js:159` | <code>"showWarning('\u4f3c\u4e4e\u65e0\u6cd5\u8fde\u63a5\u670d\u52a1\u5668')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/httpRequest.js:161` | <code>"showWarning('\u6b63\u5728\u8fde\u63a5\u670d\u52a1\u5668(' + ajaxIndex + ')')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/device.js:89` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0OTA\u72b6\u6001\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:23` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u5b57\u5178\u7c7b\u578b\u5217\u8868\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:41` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u5b57\u5178\u7c7b\u578b\u8be6\u60c5\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:60` | <code>"this.$message.error(err.msg \|\| '\u65b0\u589e\u5b57\u5178\u7c7b\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:79` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0\u5b57\u5178\u7c7b\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:98` | <code>"this.$message.error(err.msg \|\| '\u5220\u9664\u5b57\u5178\u7c7b\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:124` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u5b57\u5178\u6570\u636e\u5217\u8868\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:142` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u5b57\u5178\u6570\u636e\u8be6\u60c5\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:161` | <code>"this.$message.error(err.msg \|\| '\u65b0\u589e\u5b57\u5178\u6570\u636e\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:180` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0\u5b57\u5178\u6570\u636e\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:199` | <code>"this.$message.error(err.msg \|\| '\u5220\u9664\u5b57\u5178\u6570\u636e\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/dict.js:217` | <code>"reject(new Error(res.data?.msg \|\| '\u83b7\u53d6\u5b57\u5178\u6570\u636e\u5217\u8868\u5931\u8d25'))"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:60` | <code>"this.$message.error('\u83b7\u53d6\u4f9b\u5e94\u5668\u5217\u8868\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:92` | <code>"this.$message.error(err.msg \|\| '\u65b0\u589e\u6a21\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:109` | <code>"this.$message.error(err.msg \|\| '\u5220\u9664\u6a21\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:232` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u6a21\u578b\u914d\u7f6e\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:249` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0\u6a21\u578b\u72b6\u6001\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:272` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0\u6a21\u578b\u5931\u8d25');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:289` | <code>"this.$message.error(err.msg \|\| '\u8bbe\u7f6e\u9ed8\u8ba4\u6a21\u578b\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:317` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6\u4f9b\u5e94\u5668\u5217\u8868\u5931\u8d25');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:348` | <code>"this.$message.error(err.msg \|\| '\u65b0\u589e\u6a21\u578b\u4f9b\u5e94\u5668\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:379` | <code>"this.$message.error(err.msg \|\| '\u66f4\u65b0\u6a21\u578b\u4f9b\u5e94\u5668\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:396` | <code>"this.$message.error(err.msg \|\| '\u5220\u9664\u6a21\u578b\u4f9b\u5e94\u5668\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/apis/module/model.js:450` | <code>"this.$message.error(err.msg \|\| '\u83b7\u53d6RAG\u6a21\u578b\u5217\u8868\u5931\u8d25')"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/AddressBookDialog.vue:67` | <code>"pattern: /^[\u4e00-\u9fa5a-zA-Z0-9\\s-_]+$/,"</code> | Chinese-capable validation: The Han character range is part of the existing name-validation regex; translating it would reject supported names. |
| `src/components/CacheViewer.vue:133` | <code>"this.$message.error('\u52a0\u8f7d\u7f13\u5b58\u6570\u636e\u5931\u8d25');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ChatHistoryDialog.vue:192` | <code>"* For JSON such as {\"speaker\": \"\u672a\u77e5\u8bf4\u8bdd\u4eba\", \"content\": \"\u73b0\u5728\u51e0\u70b9\u4e86。\"}, extract content (Chinese conversation example)."</code> | Multilingual example: Representative Chinese conversation JSON illustrates content extraction; the surrounding explanation is English. |
| `src/components/CustomDialog.vue:94` | <code>"default: \"\u786e\u8ba4\u4fdd\u5b58\""</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/FunctionDialog.vue:86` | <code>"&lt;el-input v-else-if=\"field.type === 'json'\" type=\"textarea\" :rows=\"6\" placeholder=\"\u8bf7\u8f93\u5165\u5408\u6cd5\u7684 JSON\""</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ModelEditDialog.vue:232` | <code>"model.configJson[key] = &#96;\u4f60\u7684${sensitiveName}&#96;;"</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:370` | <code>"message: '\u5fc5\u987b\u8f93\u5165\u5b57\u5178\u683c\u5f0f（\u5982 {\"key\":\"value\"}），\u4fdd\u5b58\u5219\u4f7f\u7528\u539f\u6570\u636e',"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ModelEditDialog.vue:376` | <code>"message: 'JSON\u683c\u5f0f\u9519\u8bef（\u5982 {\"key\":\"value\"}），\u4fdd\u5b58\u5219\u4f7f\u7528\u539f\u6570\u636e',"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ModelEditDialog.vue:405` | <code>"api_key: \"API\u5bc6\u94a5\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:406` | <code>"personal_access_token: \"\u4e2a\u4eba\u8bbf\u95ee\u4ee4\u724c\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:407` | <code>"access_token: \"\u8bbf\u95ee\u4ee4\u724c\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:408` | <code>"token: \"\u4ee4\u724c\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:409` | <code>"secret: \"\u5bc6\u94a5\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:410` | <code>"access_key_secret: \"\u8bbf\u95ee\u5bc6\u94a5\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:411` | <code>"secret_key: \"\u5bc6\u94a5\","</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:419` | <code>"return \"\u654f\u611f\u4fe1\u606f\";"</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ModelEditDialog.vue:443` | <code>"this.$set(this.form.configJson, field, &#96;\u4f60\u7684${sensitiveName}&#96;);"</code> | Configuration placeholder data: Keep the localized sensitive-field mask labels and their prefix; the editor can submit them inside configJson. |
| `src/components/ParamDialog.vue:124` | <code>"this.$message.error('\u6570\u7ec4\u683c\u5f0f\u9519\u8bef，\u9700\u8981\u4f7f\u7528\u82f1\u6587\u5206\u53f7\u7ed3\u5c3e');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ReplacementWordDialog.vue:68` | <code>"default: '\u65b0\u589e\u66ff\u6362\u8bcd'"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/VersionFooter.vue:11` | <code>"class=\"beian-icon\" alt=\"\u5907\u6848\u56fe\u6807\"&gt;"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ViewPasswordDialog.vue:10` | <code>"\u7528\u6237\u65b0\u5bc6\u7801"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ViewPasswordDialog.vue:16` | <code>"\u7528\u6237\u65b0\u5bc6\u7801："</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ViewPasswordDialog.vue:28` | <code>"\u590d\u5236\u5bc6\u7801"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/components/ViewPasswordDialog.vue:48` | <code>"message: '\u5bc6\u7801\u5df2\u590d\u5236',"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/i18n/de.js:717` | <code>"'language.zhCN': '\u4e2d\u6587\u7b80\u4f53',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/de.js:718` | <code>"'language.zhTW': '\u4e2d\u6587\u7e41\u9ad4',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/en.js:717` | <code>"'language.zhCN': '\u4e2d\u6587\u7b80\u4f53',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/en.js:718` | <code>"'language.zhTW': '\u4e2d\u6587\u7e41\u9ad4',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/pt_BR.js:717` | <code>"'language.zhCN': '\u4e2d\u6587\u7b80\u4f53',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/pt_BR.js:718` | <code>"'language.zhTW': '\u4e2d\u6587\u7e41\u9ad4',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/vi.js:717` | <code>"'language.zhCN': '\u4e2d\u6587\u7b80\u4f53',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/i18n/vi.js:718` | <code>"'language.zhTW': '\u4e2d\u6587\u7e41\u9ad4',"</code> | Native language names: Native-script labels for the Chinese language selector; keep language.zhCN and language.zhTW values. |
| `src/registerServiceWorker.js:48` | <code>"&lt;span style=\"margin-right: 10px;\"&gt;\u53d1\u73b0\u65b0\u7248\u672c，\u70b9\u51fb\u5237\u65b0\u5e94\u7528&lt;/span&gt;"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/registerServiceWorker.js:49` | <code>"&lt;button style=\"background: white; color: #409EFF; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;\"&gt;\u5237\u65b0&lt;/button&gt;"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/utils/constant.js:2` | <code>"const HAVE_NO_RESULT = '\u6682\u65e0'"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/utils/featureManager.js:234` | <code>"remark: '\u7cfb\u7edf\u529f\u80fd\u83dc\u5355\u914d\u7f6e'"</code> | Persisted metadata: The remark is submitted to the backend with the existing parameter record; changing it would mutate persisted configuration prose. |
| `src/views/AgentTemplateManagement.vue:153` | <code>"agentCode: \"\u5c0f\u667a\","</code> | Default persona data: Keep the existing assistant name in agentCode defaults and template data; translation must not rename agents. |
| `src/views/AgentTemplateManagement.vue:234` | <code>"agentCode: \"\u5c0f\u667a\","</code> | Default persona data: Keep the existing assistant name in agentCode defaults and template data; translation must not rename agents. |
| `src/views/AgentTemplateManagement.vue:253` | <code>"agentCode: template.agentCode \|\| \"\u5c0f\u667a\","</code> | Default persona data: Keep the existing assistant name in agentCode defaults and template data; translation must not rename agents. |
| `src/views/KnowledgeBaseManagement.vue:56` | <code>"&lt;span&gt;{{&#96;\u6587\u6863&nbsp;&nbsp;${kb.documentCount \|\| 0}&#96; }}&lt;/span&gt;"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/KnowledgeBaseManagement.vue:579` | <code>"this.$message.error(data?.msg \|\| '\u53ec\u56de\u6d4b\u8bd5\u5931\u8d25');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/KnowledgeBaseManagement.vue:584` | <code>"this.$message.error(err?.data?.msg \|\| '\u53ec\u56de\u6d4b\u8bd5\u5931\u8d25');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/TemplateQuickConfig.vue:84` | <code>"agentCode: \"\u5c0f\u667a\","</code> | Default persona data: Keep the existing assistant name in agentCode defaults and template data; translation must not rename agents. |
| `src/views/TemplateQuickConfig.vue:221` | <code>"agentCode: '\u5c0f\u667a',"</code> | Default persona data: Keep the existing assistant name in agentCode defaults and template data; translation must not rename agents. |
| `src/views/VoiceCloneManagement.vue:250` | <code>"this.$message.error('\u5904\u7406\u54cd\u5e94\u65f6\u51fa\u9519');"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/VoiceCloneManagement.vue:296` | <code>"this.$message.success(this.$t('voiceClone.updateNameSuccess') \|\| '\u540d\u79f0\u66f4\u65b0\u6210\u529f');"</code> | Localized fallback: The existing localization call already runs first; retain the legacy fallback and its empty-translation behavior. |
| `src/views/VoiceCloneManagement.vue:298` | <code>"this.$message.error(res.msg \|\| this.$t('voiceClone.updateNameFailed') \|\| '\u540d\u79f0\u66f4\u65b0\u5931\u8d25');"</code> | Localized fallback: The existing localization call already runs first; retain the legacy fallback and its empty-translation behavior. |
| `src/views/VoiceCloneManagement.vue:340` | <code>"this.$message.error(this.$t('voiceClone.playFailed') \|\| '\u64ad\u653e\u5931\u8d25');"</code> | Localized fallback: The existing localization call already runs first; retain the legacy fallback and its empty-translation behavior. |
| `src/views/VoiceCloneManagement.vue:345` | <code>"this.$message.error(res.msg \|\| this.$t('voiceClone.audioNotExist') \|\| '\u97f3\u9891\u4e0d\u5b58\u5728');"</code> | Localized fallback: The existing localization call already runs first; retain the legacy fallback and its empty-translation behavior. |
| `src/views/login.vue:313` | <code>"showDanger(\"\u7528\u6237\u4fe1\u606f\u83b7\u53d6\u5931\u8d25\");"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/login.vue:374` | <code>"let errorMessage = err.data.msg \|\| \"\u767b\u5f55\u5931\u8d25\";"</code> | Localized UI: Existing user-facing copy has no exact equivalent in the locale-key audit. Keep its wording while Chinese bundles are byte-protected; no forced English UI or new keys. |
| `src/views/register.vue:340` | <code>"if (err.data != null && err.data.msg != null && err.data.msg.indexOf('\u56fe\u5f62\u9a8c\u8bc1\u7801') &gt; -1) {"</code> | Backend compatibility: The backend error substring determines whether to refresh the image captcha; keep the exact match. |
| `src/views/retrievePassword.vue:288` | <code>"if (err.data != null && err.data.msg != null && (err.data.msg.indexOf('\u56fe\u5f62\u9a8c\u8bc1\u7801') &gt; -1 \|\| err.data.msg.indexOf('Captcha') &gt; -1)) {"</code> | Backend compatibility: The backend error substring determines whether to refresh the image captcha; keep the exact match. |

## Protected locale resources

- `src/i18n/zh_CN.js`: the entire intentional Simplified Chinese locale resource, including comments. SHA256: `30935d62b9f4e0027cd298aa5e29f69bc73df4c66c8e4c3385db28acbc8a068f`.
- `src/i18n/zh_TW.js`: the entire intentional Traditional Chinese locale resource, including comments. SHA256: `4a4ce875ecd26839376885a04e3b62b2287c25a379b3956d93dad91d94e0c511`.

Both files match the Git baseline byte-for-byte. All six locale dictionaries retain the same keys and values. Only comments in `src/i18n/en.js` changed.

## User-facing static resources

- `.env`, keys `VUE_APP_TITLE`, `VUE_APP_DESCRIPTION`, and `VUE_APP_KEYWORDS`: existing localized title, product description, proper-name attribution, and SEO keywords. Keep their values.
- `public/offline.html`, title, heading, explanatory paragraphs, and retry-button text: the standalone Chinese offline page cannot rely on the Vue locale loader. Keep its UI language. Its network-status comment now uses English.
- `public/privacy-policy.html`: preserve the original Chinese user-facing privacy-policy text, date, legal references, and links. This translation slice does not revise legal terms or claim to supply an authoritative English policy.
- `public/user-agreement.html`: preserve the original Chinese user-facing agreement, legal references, and links for the same reason.
- `src/assets/xiaozhi-ai.png`, `src/assets/xiaozhi-ai_zh_CN.png`, `src/assets/xiaozhi-ai_zh_TW.png`, and `src/assets/xiaozhi-logo.png`: preserve product-branding images. Existing language-specific artwork and selection logic remain unchanged. These assets do not contain developer setup instructions.

## Bundled generator

The English [generator guide](public/generator/README.md) explains the supported settings, resource layout, and export workflow. The generator comes from a separate project; its source and reproducible build are not present in this module. The compiled bundle retains its localized UI and embedded third-party/library text. Rebuilding that source is unresolved outside this assigned write scope; no minified bundle has been hand-edited.

The following exact textual files remain unchanged. The charset is font-generation data; each model-info file contains model identifiers, wake phrases, versions, and thresholds required by its paired model. Hashes identify the retained bytes, not a directory-wide exemption.

| Exact file | SHA256 | Reason |
| --- | --- | --- |
| `public/generator/assets/index-Guo1hQ-y.js` | `41101f90ea5a59f329edbe09828b1cd36a7d8d4e8d21191b7492762a869a2366` | Compiled external generator: localized UI and embedded library output; source rebuild requires the separate project. |
| `public/generator/static/charsets/gb2312.txt` | `775f6715e94e9a6475b065fb15e37cbeebac4f234d41c34f6620ded6442054b7` | Chinese character-set data used for font generation. |
| `public/generator/static/wakenet_model/wn7_xiaoaitongxue/_MODEL_INFO_` | `4776bb347d4c68cabea7008ee99885de695da13de7be5151910dd7b73c422abe` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn7q8_xiaoaitongxue/_MODEL_INFO_` | `8277bdc66dc04b1beed040b03d48c7ce7dcc8b328dd01ca96a770546957c2f86` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn8_hilexin/_MODEL_INFO_` | `9a4a5b392b26ef07214b1d8d41887f881d442d5075684a301cc91866bac99daf` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_customword/_MODEL_INFO_` | `0adda5f3f950d6033f15e822610a50d454a7210a4449b5b3d2f06639ef6998da` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_hai1xiao3ou1_tts3/_MODEL_INFO_` | `90eb48d2bdb56134bd4acdc3965bfb8b05a29ec1840c56de62c249cd569d337e` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_haixiaowu_tts/_MODEL_INFO_` | `c5d6b4cb691839a563deeb04de961e3a5d299ee2c4fae4648e01960d70b68a1b` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_hilexin/_MODEL_INFO_` | `ac7d629244030b22d48c87324300efe4c66b27df566d82212e46c0f0061e60d7` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_hilili_tts/_MODEL_INFO_` | `5c34ae1f34b07def2f6a1367aab041a3c0b6826af553677318f12973dc7cbc70` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_himiaomiao_tts/_MODEL_INFO_` | `7a50f272621e2c7fd1907cbd1c1df7bbfe0d8bec5f2eb0dbc4c08fc3803c214d` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_hiwalle_tts2/_MODEL_INFO_` | `ab3d94d383a6174de1ccee4d8c07ea97a2db188ec127d5a266bc639fcb9a963b` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_hixiaoxing_tts/_MODEL_INFO_` | `2d9e9645fe1592cae1299202323132d01f4781fb8f8c8432ce609dcb33bea44c` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_miaomiaotongxue_tts/_MODEL_INFO_` | `05ff7ed07b6ee8fe4338084ac7549a6e81f50b1fb94dc64f7e49eed7b0a89362` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_ni3hao3xiao3mai4_tts2/_MODEL_INFO_` | `8402de9c4bcfd870ad0d381cc4739ab3fa4e428546b3cefaca3bf949cf36b9f9` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaobaiying_tts2/_MODEL_INFO_` | `82ebd4d49e92d305662608fb345435cc6a25746a7d4410bdc0e2d33e0a88a982` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaodongdong_tts2/_MODEL_INFO_` | `0e34e85e0a425a2de870e5458df0d49bcd7c249f297eb6f3035a8976c50c9a72` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaomiaoban_tts2/_MODEL_INFO_` | `1c8af6545113407cdba5579c7c408d557313671dd813dc5fb4787a6b47132c45` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaoxiaoxin_tts/_MODEL_INFO_` | `795ce53857c48f32106f80d3bcf834a8b2572d76fb4e5cf8e54d2f92c7a73f19` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaoxiaoyi_tts2/_MODEL_INFO_` | `cd51518accfaf94eceee13468224568b9384bfbb569dff83114b0962a971b182` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaoxiaozhi/_MODEL_INFO_` | `950306e13a92e9da44560ce87f733f3124ed3c971af466e1b7aa59b51cc60a14` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_nihaoxiaozhi_tts/_MODEL_INFO_` | `058c04f027862ab745c056b8c8d896396b1cf871e0a8098537610f1a0e16a108` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiao3feng1xiao3feng1_tts3/_MODEL_INFO_` | `5d19bc654a2b49b59726a3b8e547354c6c9dc4696df1e796a1ae36df93c904d3` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiao3jia1xiao3jia1_tts3/_MODEL_INFO_` | `bfe58c645e94167ad9d4a2d1d479a00988596d506505d8da9f640eb7597ce100` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaoaitongxue/_MODEL_INFO_` | `0adda5f3f950d6033f15e822610a50d454a7210a4449b5b3d2f06639ef6998da` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaobinxiaobin_tts/_MODEL_INFO_` | `52e22743fb758fe7f8e283a3822f12f797a039557ef9a2a400aaa61ee84d26c8` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaojianxiaojian_tts2/_MODEL_INFO_` | `d3cfaedf22f109087f4143bf7c23f3e07c6a21f0195b2f4943e66bded2c86705` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaokangtongxue_tts2/_MODEL_INFO_` | `72efb8d67b90977a76569d89bb4413900f4ce9cc548e60da5fe2a170ed75c89f` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaolongxiaolong_tts/_MODEL_INFO_` | `7d45fe3b2839da8638b8ae04eea4de50cc0a4aded0e7c21d9c6fd42191ab97c2` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaoluxiaolu_tts2/_MODEL_INFO_` | `b9cbec528131fef7b396ef3b0574b0242d5ddf4f6368c36d17ebc01ea8eb348c` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaomeitongxue_tts/_MODEL_INFO_` | `a6f662dbab256cd79d9c258765dd5ac7477c88e892df9c539ba4e081d6bad936` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaomingtongxue_tts2/_MODEL_INFO_` | `f1c2f767777149ea81cc30bf236f7a9c057272cb3c3e80f6cad52f5a9964da3e` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaosurou_tts2/_MODEL_INFO_` | `f364bc607e15962a160f436121129f97a5adefbb9ebc7c19f2c4b841b282a95b` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaotexiaote_tts2/_MODEL_INFO_` | `376aa921dfefe22c0b5f45e5ac920d540ced842b2682a798e0c549694fd77045` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaoyaxiaoya_tts2/_MODEL_INFO_` | `8bb56b3aac6715ef8c1083bced2cca6622f601f3d3fa61a2a92792cefdfae67b` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9_xiaoyutongxue_tts2/_MODEL_INFO_` | `f0e6e958c6817b4191f903cc6b39f5940c47f92c581f18dae433bdf3d5cf35e2` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9s_hilexin/_MODEL_INFO_` | `f90b9f63f51148a709b170bcbddd2630cd7a6639918e418aa5081b3a6d540e7e` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |
| `public/generator/static/wakenet_model/wn9s_nihaoxiaozhi/_MODEL_INFO_` | `95a971d4b3230cf79a22045ba392b55443df2f6728636685ddc61d06db987121` | Wake-word model metadata; preserve identifiers, supported spoken phrases, and numeric calibration. |

Binary fonts, speech models, emoji, and other binary images remain unchanged under the explicit asset-preservation scope.

## Verification and limitations

- Contract tests: 14 passed, including five translation/localization regression checks.
- Snapshot tests: 13 passed.
- Locale-key check: six dictionaries, 1,546 keys each.
- Node syntax checks: 109 JavaScript/Vue-script blocks passed, including the new contract test.
- Protected Chinese locale hashes and all locale values match the baseline.
- `npm test` reaches unit tests but cannot find the local `vitest` executable. `npm run build` cannot find `vue-cli-service`. These were pre-existing dependency/tooling limitations; no package installation, global tool installation, or deployment took place.
- Vue template compilation, full unit tests, rendered UI checks, and the external generator rebuild remain unverified.
- The pre-existing `voiceClone.audioNotExist` call has no matching dictionary key. Its legacy Chinese fallback remains untouched; fixing that separate localization defect is outside this behavior-preserving translation slice.

## Exact static-resource Han lines

These line ranges identify Han-bearing regions, not permission to rewrite protected locale or legal text. Categories use the integration inventory terminology.

| File | Han-bearing lines | Category |
| --- | --- | --- |
| `.env` | 1-3 | Proper name and localized product metadata |
| `public/offline.html` | 6, 57-60 | Locale resource (standalone UI) |
| `public/privacy-policy.html` | 7, 52-53, 55-56, 58-59, 61-65, 67, 69, 71-79, 81-90, 92-93, 95, 97-99, 101-103, 105-110, 112-117, 120-129, 131-135, 137-148, 150-152, 154-157, 159-162, 164-166 | Vendor/legal notice (original user-facing legal text) |
| `public/user-agreement.html` | 7, 52-53, 55-56, 58-60, 62-63, 65-68, 70-72, 74-79, 81, 83, 86-90, 92-97, 99-100, 102, 104-107, 109, 111-112, 114-127, 129-133, 135-138, 140-149, 151-152, 154, 157, 159-162, 164-171, 173-176, 178-180 | Vendor/legal notice (original user-facing legal text) |
| `src/i18n/zh_CN.js` | 2-7, 9-29, 31-52, 54-66, 68-74, 76-94, 96-99, 101-123, 125-126, 128-140, 142-160, 162-170, 172-179, 181-195, 197-218, 220-232, 234-238, 240, 243-246, 248-252, 254-276, 278-294, 296-297, 299-331, 333-351, 353-366, 368-390, 392-401, 403-404, 406-423, 425-453, 455-469, 471-520, 522-526, 528-529, 531-541, 543-578, 580-584, 586-587, 589-592, 594-629, 631-670, 672-680, 682-714, 716-718, 724-747, 749-802, 804-818, 820-827, 829-1006, 1008-1025, 1027-1053, 1055-1106, 1108-1133, 1135-1170, 1172-1210, 1212-1222, 1224-1261, 1263-1285, 1287-1307, 1309-1316, 1318-1406, 1408-1439, 1441-1463, 1465-1466, 1468-1538, 1540-1548, 1550-1570, 1572-1586, 1588-1634, 1636-1650, 1652-1653, 1655-1668, 1670-1677, 1679-1685 | Locale resource (whole protected file remains unchanged) |
| `src/i18n/zh_TW.js` | 2-7, 9-29, 31-52, 54-66, 68-74, 76-94, 96-99, 101-123, 125-126, 128-140, 142-160, 162-170, 172-179, 181-195, 197-218, 220-232, 234-238, 240, 243-246, 248-252, 254-276, 278-294, 296-297, 299-331, 333-351, 353-366, 368-390, 392-401, 403-404, 406-423, 425-453, 455-469, 471-520, 522-526, 528-529, 531-541, 543-578, 580-584, 586-587, 589-592, 594-629, 631-670, 672-680, 682-714, 716-718, 724-747, 749-802, 804-818, 820-827, 829-1006, 1008-1025, 1027-1053, 1055-1106, 1108-1133, 1135-1170, 1172-1210, 1212-1222, 1224-1261, 1263-1288, 1290-1307, 1309-1316, 1318-1406, 1408-1439, 1441-1463, 1465-1466, 1468-1538, 1540-1548, 1550-1570, 1572-1586, 1588-1634, 1636-1650, 1652-1653, 1655-1668, 1670-1677, 1679-1685 | Locale resource (whole protected file remains unchanged) |
| `public/generator/assets/index-Guo1hQ-y.js` | 35, 39, 41, 43, 45, 47, 49, 51, 55, 61, 67-69, 71, 73 | Uncompleted generated technical prose mixed with localized UI |
| `public/generator/static/charsets/gb2312.txt` | 9, 683-7445 | Locale fixture/data (font character set) |
| `public/generator/static/wakenet_model/wn7_xiaoaitongxue/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn7q8_xiaoaitongxue/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn8_hilexin/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_customword/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_hai1xiao3ou1_tts3/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_haixiaowu_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_hilexin/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_hilili_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_himiaomiao_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_hiwalle_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_hixiaoxing_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_miaomiaotongxue_tts/_MODEL_INFO_` | 2 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_ni3hao3xiao3mai4_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaobaiying_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaodongdong_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaomiaoban_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaoxiaoxin_tts/_MODEL_INFO_` | 2 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaoxiaoyi_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaoxiaozhi/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_nihaoxiaozhi_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiao3feng1xiao3feng1_tts3/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiao3jia1xiao3jia1_tts3/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaoaitongxue/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaobinxiaobin_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaojianxiaojian_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaokangtongxue_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaolongxiaolong_tts/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaoluxiaolu_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaomeitongxue_tts/_MODEL_INFO_` | 2 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaomingtongxue_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaosurou_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaotexiaote_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaoyaxiaoya_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9_xiaoyutongxue_tts2/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9s_hilexin/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |
| `public/generator/static/wakenet_model/wn9s_nihaoxiaozhi/_MODEL_INFO_` | 1 | Compatibility literal and locale fixture/data (wake model metadata) |

## Changed files

This slice changes 83 files, including this note and the added regression tests. All paths below are relative to `main/manager-web`.

- `.env.development`
- `.env.production`
- `README.md`
- `babel.config.js`
- `public/generator/README.md`
- `public/offline.html`
- `src/App.vue`
- `src/apis/api.js`
- `src/apis/httpRequest.js`
- `src/apis/module/addressBook.js`
- `src/apis/module/admin.js`
- `src/apis/module/agent.js`
- `src/apis/module/agentSnapshotApi.test.mjs`
- `src/apis/module/correctWord.js`
- `src/apis/module/device.js`
- `src/apis/module/dict.js`
- `src/apis/module/knowledgeBase.js`
- `src/apis/module/model.js`
- `src/apis/module/ota.js`
- `src/apis/module/timbre.js`
- `src/apis/module/user.js`
- `src/apis/module/voiceClone.js`
- `src/apis/module/voiceResource.js`
- `src/components/AddModelDialog.vue`
- `src/components/AgentSnapshotDialog.vue`
- `src/components/AudioPlayer.vue`
- `src/components/CacheViewer.vue`
- `src/components/ChangePasswordDialog.vue`
- `src/components/ChatHistoryDialog.vue`
- `src/components/ContextProviderDialog.vue`
- `src/components/CustomDialog.vue`
- `src/components/CustomTable.vue`
- `src/components/FirmwareDialog.vue`
- `src/components/FunctionDialog.vue`
- `src/components/HeaderBar.vue`
- `src/components/KnowledgeBaseDialog.vue`
- `src/components/ManualAddDeviceDialog.vue`
- `src/components/ModelEditDialog.vue`
- `src/components/ParamDialog.vue`
- `src/components/ProviderDialog.vue`
- `src/components/TtsAdvancedSettings.vue`
- `src/components/TtsModel.vue`
- `src/components/ViewPasswordDialog.vue`
- `src/components/VoiceCloneDialog.vue`
- `src/components/VoicePrintDialog.vue`
- `src/components/VoiceResourceDialog.vue`
- `src/i18n/en.js`
- `src/i18n/index.js`
- `src/main.js`
- `src/registerServiceWorker.js`
- `src/router/index.js`
- `src/service-worker.js`
- `src/store/index.js`
- `src/styles/global.scss`
- `src/utils/cacheViewer.js`
- `src/utils/constant.js`
- `src/utils/featureManager.js`
- `src/utils/format.js`
- `src/utils/index.js`
- `src/views/AddressBookManagement.vue`
- `src/views/AgentTemplateManagement.vue`
- `src/views/DictManagement.vue`
- `src/views/FeatureManagement.vue`
- `src/views/KnowledgeBaseItem.vue`
- `src/views/KnowledgeBaseManagement.vue`
- `src/views/ModelConfig.vue`
- `src/views/OtaManagement.vue`
- `src/views/ParamsManagement.vue`
- `src/views/ProviderManagement.vue`
- `src/views/TemplateQuickConfig.vue`
- `src/views/UserManagement.vue`
- `src/views/VoiceCloneManagement.vue`
- `src/views/VoicePrint.vue`
- `src/views/VoiceResourceManagement.vue`
- `src/views/auth.scss`
- `src/views/home.vue`
- `src/views/login.vue`
- `src/views/register.vue`
- `src/views/retrievePassword.vue`
- `src/views/roleConfig.vue`
- `vue.config.js`
- `TRANSLATION_NOTES.md`
- `tests/englishTranslationContract.test.mjs`
