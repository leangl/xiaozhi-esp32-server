// https://www.npmjs.com/package/@uni-helper/unocss-preset-uni
import { presetUni } from '@uni-helper/unocss-preset-uni'
import {
  defineConfig,
  presetAttributify,
  presetIcons,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'

export default defineConfig({
  presets: [
    presetUni({
      attributify: {
        // prefix: 'fg-', // If enabled, use the `fg-` prefix in code, e.g. <div fg-border="1px solid #000"></div>
        prefixedOnly: true,
      },
    }),
    presetIcons({
      scale: 1.2,
      warn: true,
      extraProperties: {
        'display': 'inline-block',
        'vertical-align': 'middle',
      },
    }),
    // Support CSS class attributes
    presetAttributify(),
  ],
  transformers: [
    // Enable CSS directives, including @apply, @screen, and theme()
    transformerDirectives(),
    // Enable () grouping
    // Support grouped CSS classes, e.g. `<div class="hover:(bg-gray-400 font-medium) font-(light mono)">UnoCSS test</div>`
    transformerVariantGroup(),
  ],
  shortcuts: [
    {
      center: 'flex justify-center items-center',
    },
  ],
  safelist: [],
  rules: [
    [
      'p-safe',
      {
        padding:
          'env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)',
      },
    ],
    ['pt-safe', { 'padding-top': 'env(safe-area-inset-top)' }],
    ['pb-safe', { 'padding-bottom': 'env(safe-area-inset-bottom)' }],
  ],
  theme: {
    colors: {
      /** Theme color, e.g. text-primary */
      primary: 'var(--wot-color-theme,#0957DE)',
    },
    fontSize: {
      /** Extra-small font size, e.g. text-2xs */
      '2xs': ['20rpx', '28rpx'],
      '3xs': ['18rpx', '26rpx'],
    },
  },
})
