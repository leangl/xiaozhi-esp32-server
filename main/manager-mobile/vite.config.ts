import path from 'node:path'
import process from 'node:process'
import Uni from '@dcloudio/vite-plugin-uni'
import Components from '@uni-helper/vite-plugin-uni-components'
// @see https://uni-helper.js.org/vite-plugin-uni-layouts
import UniLayouts from '@uni-helper/vite-plugin-uni-layouts'
// @see https://github.com/uni-helper/vite-plugin-uni-manifest
import UniManifest from '@uni-helper/vite-plugin-uni-manifest'
// @see https://uni-helper.js.org/vite-plugin-uni-pages
import UniPages from '@uni-helper/vite-plugin-uni-pages'
// @see https://github.com/uni-helper/vite-plugin-uni-platform
// Use with @uni-helper/vite-plugin-uni-pages
import UniPlatform from '@uni-helper/vite-plugin-uni-platform'
/**
 * Subpackage optimization and asynchronous cross-package module/component references
 * @see https://github.com/uni-ku/bundle-optimizer
 */
import Optimization from '@uni-ku/bundle-optimizer'
import dayjs from 'dayjs'
import { visualizer } from 'rollup-plugin-visualizer'
import AutoImport from 'unplugin-auto-import/vite'
import { defineConfig, loadEnv } from 'vite'
import ViteRestart from 'vite-plugin-restart'

// https://vitejs.dev/config/
export default async ({ command, mode }) => {
  // @see https://unocss.dev/
  const UnoCSS = (await import('unocss/vite')).default
  // console.log(mode === process.env.NODE_ENV) // true

  // mode: distinguish production from development
  console.log('command, mode -> ', command, mode)
  // pnpm dev:h5 yields => serve development
  // pnpm build:h5 yields => build production
  // pnpm dev:mp-weixin yields => build development (note: command is build)
  // pnpm build:mp-weixin yields => build production
  // pnpm dev:app yields => build development (note: command is build)
  // pnpm build:app yields => build production
  // dev and build use .env.development and .env.production respectively

  const { UNI_PLATFORM } = process.env
  console.log('UNI_PLATFORM -> ', UNI_PLATFORM) // Produces mp-weixin, h5, app, etc.

  const env = loadEnv(mode, path.resolve(process.cwd(), 'env'))
  const {
    VITE_APP_PORT,
    VITE_SERVER_BASEURL,
    VITE_DELETE_CONSOLE,
    VITE_SHOW_SOURCEMAP,
    VITE_APP_PUBLIC_BASE,
    VITE_APP_PROXY,
    VITE_APP_PROXY_PREFIX,
  } = env
  console.log('Environment variables env -> ', env)

  return defineConfig({
    envDir: './env', // Custom environment directory
    base: VITE_APP_PUBLIC_BASE,
    plugins: [
      UniPages({
        exclude: ['**/components/**/**.*'],
        // Set homePage with type="home" in a Vue route block
        // Pages live in src/pages; subpackages must be outside that directory
        subPackages: ['src/pages-sub'], // Array of subpackage directories; none may be inside pages
        dts: 'src/types/uni-pages.d.ts',
      }),
      UniLayouts(),
      UniPlatform(),
      UniManifest(),
      // Register UniXXX plugins before Uni
      {
        // Temporary workaround for an official @dcloudio/uni-mp-compiler compilation bug
        // See GitHub issue: https://github.com/dcloudio/uni-app/issues/4952
        // Disable vite:vue devToolsEnabled and force inline=true when compiling Vue templates
        name: 'fix-vite-plugin-vue',
        configResolved(config) {
          const plugin = config.plugins.find(p => p.name === 'vite:vue')
          if (plugin && plugin.api && plugin.api.options) {
            plugin.api.options.devToolsEnabled = false
          }
        },
      },
      UnoCSS(),
      AutoImport({
        imports: ['vue', 'uni-app'],
        dts: 'src/types/auto-import.d.ts',
        dirs: ['src/hooks'], // Auto-import hooks
        vueTemplate: true, // default false
      }),
      // Optimization needs page.json, so run it after UniPages
      Optimization({
        enable: {
          'optimization': true,
          'async-import': true,
          'async-component': true,
        },
        dts: {
          base: 'src/types',
        },
        logger: false,
      }),

      ViteRestart({
        // Apply vite.config.js changes without restarting manually
        restart: ['vite.config.js'],
      }),
      // Add BUILD_TIME and BUILD_BRANCH on H5
      UNI_PLATFORM === 'h5' && {
        name: 'html-transform',
        transformIndexHtml(html) {
          return html.replace('%BUILD_TIME%', dayjs().format('YYYY-MM-DD HH:mm:ss'))
        },
      },
      // Bundle analysis popup for H5 production builds only
      UNI_PLATFORM === 'h5'
      && mode === 'production'
      && visualizer({
        filename: './node_modules/.cache/visualizer/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
      // Enable copyNativeRes only on the App platform
      // UNI_PLATFORM === 'app' && copyNativeRes(),
      Components({
        extensions: ['vue'],
        deep: true, // Whether to scan subdirectories recursively
        directoryAsNamespace: false, // Whether directory names prefix the component namespace; true yields directory name + component name
        dts: 'src/types/components.d.ts', // Generated component type declaration path (TypeScript support)
      }),
      Uni(),
    ],
    define: {
      __UNI_PLATFORM__: JSON.stringify(UNI_PLATFORM),
      __VITE_APP_PROXY__: JSON.stringify(VITE_APP_PROXY),
    },
    css: {
      postcss: {
        plugins: [
          // autoprefixer({
          //      // Target browsers
          //   overrideBrowserslist: ['> 1%', 'last 2 versions'],
          // }),
        ],
      },
    },

    resolve: {
      alias: {
        '@': path.join(process.cwd(), './src'),
        '@img': path.join(process.cwd(), './src/static/images'),
      },
    },
    server: {
      host: '0.0.0.0',
      hmr: true,
      port: Number.parseInt(VITE_APP_PORT, 10),
      // H5 only; other platforms use build rather than devServer
      proxy: JSON.parse(VITE_APP_PROXY)
        ? {
            [VITE_APP_PROXY_PREFIX]: {
              target: VITE_SERVER_BASEURL,
              changeOrigin: true,
              rewrite: path => path.replace(new RegExp(`^${VITE_APP_PROXY_PREFIX}`), ''),
            },
          }
        : undefined,
    },
    esbuild: {
      drop: VITE_DELETE_CONSOLE === 'true' ? ['console', 'debugger'] : ['debugger'],
    },
    build: {
      sourcemap: false,
      // Help debug non-H5 platforms
      // sourcemap: VITE_SHOW_SOURCEMAP === 'true', // Defaults to false
      target: 'es6',
      // Do not minify in development
      minify: mode === 'development' ? false : 'esbuild',

    },
  })
}
