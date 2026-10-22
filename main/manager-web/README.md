# xiaozhi manager web

This guide covers frontend development. For server deployment, see the [repository README](../../README.md).

## Project setup

Open `main/manager-web` as the project directory in your code editor, then install the project dependencies:

```sh
npm install
```

## Development

```sh
npm run serve
```

The development server uses port 8001. Configure the API address in `.env.development`. To redirect mobile browsers to the H5 application, follow the comments beside `VUE_APP_H5_URL` in that file; the mobile application remains a separate project.

## Production build

```sh
npm run build
```

Configure production settings in `.env.production`. This command builds frontend assets; it does not deploy them or restart services.

## Checks

```sh
npm run check:i18n
npm run test:contract
npm run test:snapshot
npm run test:unit
```

`npm test` runs contract tests followed by Vitest unit tests. Snapshot regression tests and locale-key validation have separate scripts. Contract and snapshot tests use Node's built-in test runner. Unit tests and production builds require the local dependencies from `package.json`; no global Vue CLI or Vitest installation is needed.

## Configuration and bundled resources

See the [Vue CLI configuration reference](https://cli.vuejs.org/config/) for build settings.

The [firmware asset generator guide](public/generator/README.md) explains the separately built static generator, its resource directories, and how to export `assets.bin`.

## Translation boundaries

Maintainer-facing comments, diagnostics, and development instructions use English. Locale selection, `zh_CN` fallback behavior, request-language headers, routes, permissions, and API fields retain their existing behavior.

The Chinese locale files `src/i18n/zh_CN.js` and `src/i18n/zh_TW.js` remain byte-for-byte unchanged, including comments. The native Chinese language names at `language.zhCN` and `language.zhTW` in the other dictionaries remain language-selection data. Existing locale keys replace equivalent inline UI text; this change adds no dictionary keys or values.

See [translation exceptions](TRANSLATION_NOTES.md) for the exact remaining localized text and compatibility data. The preserved Chinese legal pages, offline page, branding, and model assets are user-facing resources, not untranslated development instructions. The notes do not authorize changing those resources, deploying a build, or removing service integrations.
