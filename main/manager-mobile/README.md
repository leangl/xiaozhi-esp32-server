## Mobile Management Console (manager-mobile)

A cross-platform management client built with uni-app v3, Vue 3, and Vite. It supports native Android/iOS apps and WeChat mini-programs.

### Platform compatibility

| H5 | iOS | Android | WeChat mini-program |
| -- | --- | ------- | ------------------- |
| Yes | Yes | Yes | Yes |

UI component support varies slightly by platform. Consult the relevant component library documentation.

### Development requirements

- Node >= 18
- pnpm >= 7.30 (prefer the project's declared `pnpm@10.x`)
- Optional: HBuilderX for native debugging/packaging; WeChat Developer Tools for mini-programs

### Quick start

1. Configure environment variables in `env/.env.development`. If your checkout includes `env/.env.example`, copy it first; otherwise use the existing development file. Adjust `VITE_SERVER_BASEURL`, `VITE_UNI_APPID`, and `VITE_WX_APPID` for your environment.
2. Install dependencies when authorized:

   ```bash
   pnpm i
   ```

   The package's `prepare` script runs `git init && husky`. Do not run installation or prepare hooks in a shared checkout unless that Git/hook setup is intended. Translation validation does not require installation.
3. Start local development with hot reload:

   - H5: `pnpm dev:h5`; use the IP address and port printed in the startup log.
   - WeChat: `pnpm dev:mp` or `pnpm dev:mp-weixin`; import `dist/dev/mp-weixin` into WeChat Developer Tools.
   - Native App: import `manager-mobile` into HBuilderX and follow the local debugging instructions below.

### Environment variables and configuration

Environment files live in the custom `env` directory and follow Vite naming conventions, such as `.env.development` and `.env.production`.

- `VITE_APP_TITLE`: app name, consumed by `manifest.config.ts`
- `VITE_UNI_APPID`: uni-app AppID for native apps
- `VITE_WX_APPID`: WeChat mini-program AppID
- `VITE_FALLBACK_LOCALE`: default language, such as `zh-Hans`
- `VITE_SERVER_BASEURL`: backend base URL for HTTP requests
- `VITE_DELETE_CONSOLE`: whether builds remove console calls (`true`/`false`)
- `VITE_SHOW_SOURCEMAP`: whether to generate source maps (disabled by default)
- `VITE_LOGIN_URL`: login page used by the route interceptor

Example for `env/.env.development`:

```env
VITE_APP_TITLE=小智
VITE_FALLBACK_LOCALE=zh-Hans
VITE_UNI_APPID=
VITE_WX_APPID=

VITE_SERVER_BASEURL=http://localhost:8080

VITE_DELETE_CONSOLE=false
VITE_SHOW_SOURCEMAP=false
VITE_LOGIN_URL=/pages/login/index
```

The example preserves the localized Xiaozhi app name. `manifest.config.ts` reads the title, AppIDs, and language from `env`.

### Configuration required before a future deployment

These are reference instructions, not authorization to create accounts, build, or deploy.

1. App IDs:

   - Obtain `VITE_UNI_APPID` from the [DCloud Developer Center](https://dev.dcloud.net.cn/).
   - Obtain `VITE_WX_APPID` by registering a mini-program on the [WeChat platform](https://mp.weixin.qq.com/).
2. Server URL: set `VITE_SERVER_BASEURL` to your backend URL.
3. App information: set `VITE_APP_TITLE` and update icon assets such as `src/static/logo.png`.
4. Other settings: review `manifest.config.ts` and, if necessary, the tab bar in `src/layouts/fg-tabbar/tabbarList.ts`.

### Detailed setup guide

The original screenshots below retain their existing filenames and UI language. The adjacent English instructions describe the complete workflow; renaming the shared image assets is outside this module's scope.

#### Obtain a uni-app AppID

![Generate an AppID](../../docs/images/manager-mobile/生成appid.png)

Create/select the app in the DCloud Developer Center, obtain its generated AppID, and copy that value into `VITE_UNI_APPID`.

The screenshot shows HBuilderX's visual editor for `src/manifest.json`, under **Basic Configuration**. The highlighted **uni-app application identifier (AppID)** field has a **Retrieve Again** button and a link explaining DCloud AppIDs. The other basic fields are **Application Name**, **Application Description**, **Version Name**, **Version Code**, and **Vue Version**. The sidebar groups icons, launch screens, modules, permissions, native plugins, other platform settings, Harmony, Web, and mini-program settings. In this repository the manifest is generated: keep persistent values in the environment/source configuration rather than editing generated output by hand.

#### Run locally

![Local debugging](../../docs/images/manager-mobile/本地运行.png)

1. Import the `manager-mobile` directory into HBuilderX.
2. Ask HBuilderX to recognize the project type again.
3. Connect a phone or use an emulator to debug the app.

The highlighted menu is **Run → Run on Phone or Emulator**. Choose the Android App runtime, iOS App runtime, or iOS Simulator runtime; each also has a **Specified Page** variant. Harmony is another visible target. Other debugging menu items include the WebView console, custom debug runtime, Android emulator port, ADB path, and automatically opening Vue Devtools. Choose only an already configured target appropriate to your environment; this guide does not provision devices or accounts.

![Recognize the project type again](../../docs/images/manager-mobile/重新识别项目.png)

If HBuilderX does not recognize the project, right-click the project root and choose **Re-identify project type**. Confirm that it is recognized as a **uni-app** project.

### Routing and authentication

- `src/main.ts` registers the `routeInterceptor` routing plugin.
- The interceptor uses a denylist: it checks only pages configured to require login, as returned by `getNeedLoginPages` in `@/utils`.
- Login state comes from Pinia's `useUserStore`. Unauthenticated users are redirected to `VITE_LOGIN_URL`, with a parameter for returning to the original page.

### HTTP requests

- `alova` and `@alova/adapter-uniapp` provide the shared instance in `src/http/request/alova.ts`.
- `getEnvBaseUrl` reads the environment configuration and runtime server override. `method.config.meta.domain` can select a different domain.
- Authentication normally reads `uni.getStorageSync('token')` and supplies the `Authorization` header. Missing credentials redirect to login.
- The response handler distinguishes HTTP errors (`statusCode !== 200`) from application errors (`code !== 0`). A `401` clears the token and redirects to login.
- See [HTTP client usage](src/http/README.md) and [translation compatibility notes](TRANSLATION_NOTES.md).

### Build and release reference

Native builds and publication require the appropriate platform tools/accounts and separate authorization.

#### WeChat mini-program

1. Configure `VITE_WX_APPID`.
2. Run `pnpm build:mp`; output is written to `dist/build/mp-weixin`.
3. Import that directory into WeChat Developer Tools and upload the code.
4. Submit the mini-program for review on the WeChat platform.

#### Android and iOS apps

Prepare packaging:

![App packaging: preparation](../../docs/images/manager-mobile/打包发行步骤1.png)

1. Configure `VITE_UNI_APPID`.
2. Run `pnpm build:app`; output is written to `dist/build/app`.
3. Import the project into HBuilderX.
4. Choose **Release → App-Android/iOS - Cloud Packaging**.

The highlighted Release menu also offers **View Cloud Packaging Status**, **Android/iOS Local Packaging**, and **Harmony Local Packaging**. The remaining entries publish other targets (mini-programs, Quick Apps, Harmony services, or Web), create an app update package, customize release steps, or manage published Web files; they are not steps in this native cloud-packaging workflow.

Configure packaging:

![App packaging: options](../../docs/images/manager-mobile/打包发行步骤2.png)

1. Upload the app icon and launch-screen images.
2. Set the version number and version name.
3. Supply signing credentials: an Android keystore, or iOS developer certificates and provisioning profiles.
4. Set the package name/Bundle ID.
5. Select a test or release package.
6. Choose **Package** to start cloud packaging.

The packaging dialog shows the application name/version, a **Modify Manifest Configuration** link, Android APK/iOS IPA target checkboxes, and platform settings tabs. Android signing choices are **Use Own Certificate**, **Use Cloud Certificate**, or **Use Public Test Certificate**. Own-certificate fields are **Certificate File**, **Keystore Password**, **Certificate Alias**, and **Private-Key Password**; **Browse** selects the file. Optional channel packages include None, Google Play AAB, Tencent App Store, 360, Huawei, Xiaomi, OPPO, and VIVO. Anti-re-signing options cover AppID, package name, and certificate. These are descriptions of the original controls, not recommendations to change signing or distribution settings.

Other controls choose a **Release Package** or **Custom Debug Runtime** (iOS Safari debugging requires Apple development signing), generate iOS dSYM files or source maps, enable native obfuscation for configured JS/nvue files, and opt into the advertising network. At the bottom, **Traditional Packaging** uploads code/certificates, while **Fast Secure Packaging** is described as not uploading them and packaging faster. Their **Details** links explain the vendor's claims. Review the applicable platform/vendor documentation before any separately authorized packaging operation; no option is enabled by this translation.

For a future store release, upload the APK to the appropriate Android marketplaces, or upload the IPA through App Store Connect (an Apple developer account is required).

### Project conventions

- Pages/subpackages: generated by `@uni-helper/vite-plugin-uni-pages` and `pages.config.ts`; tab bar settings live in `src/layouts/fg-tabbar/tabbarList.ts`.
- Component/hook auto-imports: see `unplugin-auto-import` and `@uni-helper/vite-plugin-uni-components` in `vite.config.ts`.
- Styles: UnoCSS and `src/style/index.scss`.
- State: Pinia with `pinia-plugin-persistedstate`.
- Code quality: ESLint, Husky, and lint-staged; lint-staged formats files before commits when hooks are installed.

### Common commands

```bash
# Development
pnpm dev:mp        # Alias of dev:mp-weixin

# Build
pnpm build:mp      # Alias of build:mp-weixin

# Validation (no prepare or Git initialization required)
pnpm test:snapshot
pnpm type-check
pnpm lint

# Formatting changes files; run only when intended
pnpm lint:fix
```

### License

MIT
