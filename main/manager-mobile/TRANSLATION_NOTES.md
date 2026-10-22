# English translation and compatibility notes

This module's maintained comments, developer diagnostics, and technical guides are in English. Translation does not remove uni-app, DCloud, WeChat, or any backend integration. Network behavior, permissions, error codes, client-facing identifiers, and supported languages are unchanged.

The remaining Chinese text is retained at the exact surfaces below. Quoted originals in this document are reference data, not untranslated instructions. These exceptions do not exempt other text in the same directories.

## Protected locale and legal originals

- `src/i18n/zh_CN.ts` and `src/i18n/zh_TW.ts` are byte-for-byte protected locale dictionaries, including their existing comments. The explicit locale-file integrity requirement takes precedence over comment translation within these two files.
- `src/pages/login/privacy-policy-zh.vue` and `src/pages/login/user-agreement-zh.vue` are original Chinese legal documents, including their route titles. They remain unchanged. Existing English documents are available at [privacy-policy-en.vue](src/pages/login/privacy-policy-en.vue) and [user-agreement-en.vue](src/pages/login/user-agreement-en.vue); this translation makes no new legal-equivalence claim.
- `src/i18n/index.ts`, `getSupportedLanguages()`: `简体中文` means Simplified Chinese and `繁體中文` means Traditional Chinese. Language names remain in their native scripts so users can recognize them.
- `src/pages/login/index.vue` and `src/pages/register/index.vue`: `selectedAreaName` and the fallback `mobileAreaList` use `中国大陆` (Mainland China), paired with the unchanged calling code `+86`. This is region-list data, not a diagnostic or identifier to translate.

## Native startup labels and generated configuration

Static labels are localized startup/fallback UI. Existing runtime navigation/tab-bar updates continue to use i18n. Do not import runtime stores into build-time configuration merely to remove these literals.

| Source and field | Original value | English meaning |
| --- | --- | --- |
| `env/.env`, `VITE_APP_TITLE`; `pages.config.ts`, `globalStyle.navigationBarTitleText` | `小智` | Xiaozhi (app name) |
| `src/layouts/fg-tabbar/tabbarList.ts`, the three `text` fields | `首页`, `配网`, `系统` | Home, Network Configuration, System |
| `src/pages/index/index.vue`, route title | `首页` | Home |
| `src/pages/agent/index.vue`, route title | `智能体` | Agent |
| `src/pages/agent/provider.vue`, route title | `编辑源` | Edit Source |
| `src/pages/agent/speedPitch.vue`, route title | `语音设置` | Voice Settings |
| `src/pages/agent/tools.vue`, route title | `编辑功能` | Edit Functions |
| `src/pages/chat-history/detail.vue`, route title | `聊天详情` | Chat Details |
| `src/pages/device-config/index.vue`, route title | `设备配置` | Device Configuration |
| `src/pages/register/index.vue`, route title | `注册` | Register |
| `src/pages/settings/index.vue`, route title | `设置` | Settings |
| `src/pages-sub/demo/index.vue`, route title and demo label | `分包页面`, `分包页面demo` | Subpackage Page, Subpackage Page Demo |

`src/pages.json` is generated route/tab configuration and retains the corresponding labels above, plus `隐私政策` (Privacy Policy) and `用户协议` (User Agreement) for the protected legal pages. `src/manifest.json` retains the app name and permission explanation from their sources. Neither generated file needs regeneration for comment/diagnostic-only source changes; do not hand-edit generated output.

`manifest.config.ts`, `mp-weixin.permission['scope.userLocation'].desc`, and its generated counterpart retain `WiFi配网功能需要获取位置权限`: **Wi-Fi provisioning requires location access.** This is an OS-facing localized permission explanation. Permission keys and requested capabilities are unchanged.

## Parsed application-error contract

`src/http/request/alova.ts` constructs `请求错误[${code}]：${msg}` (Request error [code]: message). Preserve the entire prefix, brackets, full-width colon, placeholders, and numeric codes. These callers parse exact substrings:

- `src/pages/voiceprint/index.vue`: `请求错误[10054]`, voiceprint API not configured.
- `src/pages/forgot-password/index.vue`: `请求错误[10067]`, invalid image CAPTCHA, in both SMS and password-reset paths.
- `src/pages/register/index.vue`: `请求错误[10067]`, invalid image CAPTCHA, and `请求错误[10070]`, phone number already registered.

Translating the prefix alone would silently break those branches. A future structured-error migration would need compatible producers and consumers and is outside this translation.

## Localized error and UI fallbacks without existing dictionary keys

These strings are currently presented to users. Preserve their Chinese output instead of silently making the Chinese UI English. Moving them into dictionaries would require adding protected locale values and separate approval; no such values were added here.

`src/http/request/alova.ts`:

- `无法配置http协议地址,请检查接口地址`: Cannot configure an HTTP URL; check the API address.
- `[请求错误]：未登录`: [Request error]: Not logged in.
- `HTTP请求错误[${statusCode}]`: HTTP request error [statusCode].

`src/http/request/enum.ts`, `ShowMessage()`:

| Original message | English meaning |
| --- | --- |
| `请求错误(400)` | Request error (400) |
| `未授权，请重新登录(401)` | Unauthorized; sign in again (401) |
| `拒绝访问(403)` | Access denied (403) |
| `请求出错(404)` | Request failed (404) |
| `请求超时(408)` | Request timeout (408) |
| `服务器错误(500)` | Server error (500) |
| `服务未实现(501)` | Service not implemented (501) |
| `网络错误(502)` | Network error (502) |
| `服务不可用(503)` | Service unavailable (503) |
| `网络超时(504)` | Network timeout (504) |
| `HTTP版本不受支持(505)` | HTTP version not supported (505) |
| `混合内容错误(600)` | Mixed-content error (600) |
| `连接出错(${status})!` | Connection error (status)! |
| `${message}，请检查网络或联系管理员！` | Append: Please check the network or contact the administrator! |

Other exact UI fallbacks:

- `src/hooks/useUpload.ts`, oversized-file toast: `文件大小不能超过 ${maxSize / 1024 / 1024}MB` means **File size must not exceed [limit] MB**. Preserve the size calculation, space, and unit.
- `src/utils/uploadFile.ts`, oversized-file warning: `文件大小不能超过${maxSize}MB` has the same meaning, with the existing MB-valued parameter and no inserted space.
- `src/pages/voiceprint/index.vue`, missing selection details: `已选择: ${audioId.substring(0, 8)}...` means **Selected: [first eight ID characters]...**. Preserve truncation and punctuation.
- The same page's missing-description label, `暂无描述`, means **No description available**.

Existing keys are reused for the four agent tab labels, agent selection prompts, and the zero-second audio-duration label. No Chinese locale dictionary bytes were changed.

## Attribution, asset identifiers, and linked screenshots

- `package.json`, `author.zhName`: `黄俊森` is the author's original name, retained as attribution rather than transliterated.
- `src/router/interceptor.ts` and `src/utils/platform.ts`: `菲鸽` is the original contributor name. Surrounding attribution labels are English.
- `src/static/logo.svg`: `_图层_2` and `_图层_1-2` are existing SVG element IDs, retained to preserve references. Their human-readable `data-name` labels are translated to **Layer 2** and **Layer 1**. Geometry, CSS classes, and appearance are unchanged.
- The README links to five original screenshots outside this module: `生成appid.png`, `本地运行.png`, `重新识别项目.png`, `打包发行步骤1.png`, and `打包发行步骤2.png` under `../../docs/images/manager-mobile/`. Their filenames mean **Generate AppID**, **Run Locally**, **Re-identify Project**, and **Packaging Steps 1/2**. The README supplies adjacent English instructions for each workflow. The image files and references remain intact; this module does not rename shared assets.
