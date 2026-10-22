import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const localeNames = ['zh_CN', 'zh_TW', 'en', 'de', 'vi', 'pt_BR'];
const locales = Object.fromEntries(localeNames.map((name) => {
  const source = read(`src/i18n/${name}.js`).replace('export default', 'globalThis.messages =');
  const context = {};
  runInNewContext(source, context);
  return [name, context.messages];
}));

const reusedKeys = [
  'common.cancel', 'common.action', 'common.deleteCancelled', 'common.addProvider',
  'paramManagement.select', 'paramManagement.addParam', 'paramManagement.getParamsListFailed',
  'user.status', 'cache.cached', 'cache.notCached', 'functionDialog.copyFailed',
  'functionDialog.loading', 'voicePrintDialog.addSpeaker',
  'voicePrintDialog.requiredDescription', 'voicePrintDialog.requiredName',
  'voicePrintDialog.requiredAudioVector', 'mcpToolCall.inputPlaceholder', 'button.close',
  'templateQuickConfig.agentSettings.agentNamePlaceholder',
  'templateQuickConfig.agentSettings.systemPromptPlaceholder',
  'dictTypeDialog.addDictType', 'dictDataDialog.addDictData',
  'knowledgeFileUpload.getListFailed', 'otaManagement.addFirmware',
  'retrievePassword.captcha', 'register.captchaLoadFailed', 'roleConfig.fetchPluginsFailed',
];

test('reused inline-UI keys exist in all six locale dictionaries', () => {
  for (const [name, messages] of Object.entries(locales)) {
    for (const key of reusedKeys) {
      assert.equal(typeof messages[key], 'string', `${name}: ${key}`);
      assert.ok(messages[key].length, `${name}: ${key} must not be empty`);
    }
  }
});

test('dynamic model placeholders retain the field label in every language', () => {
  for (const [name, messages] of Object.entries(locales)) {
    assert.match(messages['mcpToolCall.inputPlaceholder'], /\{label\}/, name);
  }
  for (const file of ['AddModelDialog.vue', 'ModelEditDialog.vue']) {
    assert.match(read(`src/components/${file}`), /\$t\('mcpToolCall\.inputPlaceholder', \{ label: f\.key \}\)/);
  }
});

test('localized prop defaults use the Vue component translation context', () => {
  for (const file of ['CustomDialog.vue', 'CustomTable.vue', 'ParamDialog.vue', 'VoicePrintDialog.vue']) {
    const source = read(`src/components/${file}`);
    const defaults = [...source.matchAll(/default\(\) \{ return this\.\$t\('([^']+)'\); \}/g)];
    assert.ok(defaults.length, `${file} must expose a localized default`);
    for (const [factory, key] of defaults) {
      const options = runInNewContext(`({ ${factory} })`);
      for (const messages of Object.values(locales)) {
        assert.equal(options.default.call({ $t: (value) => messages[value] }), messages[key]);
      }
    }
  }
});

test('backend captcha compatibility matching and Chinese name validation remain intact', () => {
  const captchaLiteral = String.fromCodePoint(0x56fe, 0x5f62, 0x9a8c, 0x8bc1, 0x7801);
  for (const file of ['register.vue', 'retrievePassword.vue']) {
    assert.ok(read(`src/views/${file}`).includes(`indexOf('${captchaLiteral}') > -1`));
  }
  const nameRange = String.fromCodePoint(0x4e00) + '-' + String.fromCodePoint(0x9fa5);
  assert.ok(read('src/components/AddressBookDialog.vue').includes(`pattern: /^[${nameRange}a-zA-Z0-9\\s-_]+$/`));
});

test('locale fallback, language IDs and Accept-Language formatting remain intact', () => {
  const loader = read('src/i18n/index.js');
  assert.match(loader, /fallbackLocale: 'zh_CN'/);
  assert.match(loader, /browserLang === 'zh-TW' \|\| browserLang === 'zh-HK' \|\| browserLang === 'zh-MO'/);
  const request = read('src/apis/httpRequest.js');
  assert.match(request, /currentLang\.replace\('_', '-'\)/);
  assert.match(request, /acceptLanguage = 'en-US'/);
});
