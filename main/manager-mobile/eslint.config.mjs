import uniHelper from '@uni-helper/eslint-config'

export default uniHelper({
  unocss: true,
  vue: true,
  markdown: false,
  ignores: [
    'src/uni_modules/',
    'dist',
    // Generated unplugin-auto-import types change on each commit; exclude them here and in .gitignore
    'auto-import.d.ts',
    // Generated vite-plugin-uni-pages types vary across branches; exclude them in .gitignore
    'uni-pages.d.ts',
    // Plugin-generated files
    'src/pages.json',
    'src/manifest.json',
    // Ignore generated files
    'src/service/app/**',
  ],
  rules: {
    'no-console': 'off',
    'no-unused-vars': 'off',
    'vue/no-unused-refs': 'off',
    'unused-imports/no-unused-vars': 'off',
    'eslint-comments/no-unlimited-disable': 'off',
    'jsdoc/check-param-names': 'off',
    'jsdoc/require-returns-description': 'off',
    'ts/no-empty-object-type': 'off',
    'no-extend-native': 'off',
  },
  formatters: {
    /**
     * Format CSS, LESS, SCSS files, also the `<style>` blocks in Vue
     * By default uses Prettier
     */
    css: true,
    /**
     * Format HTML files
     * By default uses Prettier
     */
    html: true,
  },
})
