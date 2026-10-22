import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

// Offline translation-sidecar checks. HEAD is the pre-translation contract;
// these tests neither import application entry points nor start a provider.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const prefix = 'main/digital-human/';
const files = execFileSync('git', ['ls-files', prefix], { cwd: root, encoding: 'utf8' })
    .trim().split('\n').filter(Boolean).map(path => path.slice(prefix.length));
const vendorJavaScript = new Set([
    'js/utils/libopus.js',
    'js/live2d/pixi.js',
    'js/live2d/live2dcubismcore.min.js',
    'js/live2d/cubism4.min.js',
]);
const javaScript = files.filter(path => path.endsWith('.js') && !vendorJavaScript.has(path));
const python = files.filter(path => path.endsWith('.py'));
const current = path => readFileSync(resolve(root, prefix, path), 'utf8');
const baseline = path => execFileSync('git', ['show', `HEAD:${prefix}${path}`], { cwd: root, encoding: 'utf8' });
const importSource = source => import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const matches = (source, pattern) => [...source.matchAll(pattern)].map(match => match[0]);
const withoutCssComments = source => source.replace(/\/\*[\s\S]*?\*\//g, '').trim();

test('all first-party JavaScript and inline scripts pass syntax checks without execution', () => {
    const failures = [];
    const sources = javaScript.map(path => [path, current(path)]);
    for (const [index, match] of [...current('index.html').matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)].entries()) {
        if (!/\bsrc\s*=/.test(match[1])) sources.push([`index.html inline script ${index}`, match[2]]);
    }
    for (const [path, source] of sources) {
        const result = spawnSync(process.execPath, ['--input-type=module', '--check'], { input: source, encoding: 'utf8' });
        if (result.status !== 0) failures.push(`${path}: ${result.error?.message || result.stderr}`);
    }
    assert.ok(sources.length > 0);
    assert.deepEqual(failures, []);
});

test('all first-party Python parses and preserves AST logic, keys, and f-string expressions', () => {
    const source = `import ast, json, sys
files = json.load(sys.stdin)
for path, versions in files.items():
    old, new = [ast.parse(value, filename=path) for value in versions]
    compile(new, path, 'exec')
    old_values = [node.value for node in ast.walk(old) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    new_values = [node.value for node in ast.walk(new) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert len(old_values) == len(new_values), path + ': string count changed'
    for before, after in zip(old_values, new_values):
        if not any('\\u3400' <= ch <= '\\u9fff' for ch in before):
            assert before == after, path + ': non-Chinese string/identifier changed'
    for tree in (old, new):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                node.value = '<translated string>'
    assert ast.dump(old) == ast.dump(new), path + ': Python AST logic or interpolation changed'
print(str(len(files)) + ' Python files parsed; AST contracts preserved')
`;
    const result = spawnSync(process.env.PYTHON || 'python3', ['-c', source], {
        input: JSON.stringify(Object.fromEntries(python.map(path => [path, [baseline(path), current(path)]]))),
        encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.error?.message || result.stderr);
    assert.ok(python.length > 0);
});

test('dependency-free config module preserves wake phrases and persisted configuration behavior', async () => {
    const old = await importSource(baseline('js/config/manager.js'));
    const translated = await importSource(current('js/config/manager.js'));
    assert.equal(translated.DEFAULT_WAKE_WORDS, old.DEFAULT_WAKE_WORDS);
    assert.ok(old.DEFAULT_WAKE_WORDS.split('\n').length > 1);
    function exercise(module) {
        const ids = ['deviceMac', 'deviceName', 'clientId', 'otaUrl', 'serverUrl', 'wakewordWsUrl', 'wakewordEnabled', 'wakewordList', 'emojiEnabled'];
        const elements = Object.fromEntries(ids.map(id => [id, { value: '' }]));
        const storage = new Map([
            ['xz_tester_deviceMac', 'AA:BB:CC:DD:EE:FF'],
            ['xz_tester_deviceName', '  local avatar  '],
            ['xz_tester_clientId', '  test-client  '],
            ['xz_tester_otaUrl', 'http://localhost:8002/xiaozhi/ota/'],
            ['xz_tester_wakewordWsUrl', 'ws://localhost:8006/wakeword-ws'],
            ['xz_tester_wakewordEnabled', 'false'],
            ['xz_tester_emojiEnabled', 'false'],
        ]);
        const saved = Object.fromEntries(['document', 'localStorage'].map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
        try {
            globalThis.document = { getElementById: id => elements[id] || null };
            globalThis.localStorage = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, String(value)) };
            module.loadConfig();
            assert.equal(elements.wakewordList.value, module.DEFAULT_WAKE_WORDS);
            elements.serverUrl.value = ' ws://localhost:8000/xiaozhi/v1/ ';
            module.saveConfig();
            module.saveConnectionUrls();
            const config = module.getConfig();
            assert.equal(config.deviceId, config.deviceMac);
            assert.equal(config.deviceName, 'local avatar');
            assert.equal(config.emojiEnabled, false);
            return { config, elements, storage: [...storage] };
        } finally {
            for (const [key, descriptor] of Object.entries(saved)) {
                if (descriptor) Object.defineProperty(globalThis, key, descriptor);
                else delete globalThis[key];
            }
        }
    }
    assert.deepEqual(exercise(translated), exercise(old));
});

test('dependency-free queue preserves batching, waiting, timeout, and clear behavior', async () => {
    const OldQueue = (await importSource(baseline('js/utils/blocking-queue.js'))).default;
    const Queue = (await importSource(current('js/utils/blocking-queue.js'))).default;
    async function exercise(Constructor) {
        const queue = new Constructor();
        let settled = false;
        const first = queue.dequeue().then(value => { settled = true; return value; });
        await Promise.resolve();
        assert.equal(settled, false);
        queue.enqueue('first');
        const initial = await first;
        queue.enqueue('a');
        const batch = queue.dequeue(3, 1000);
        queue.enqueue('b', 'c');
        const batched = await batch;
        queue.enqueue('partial');
        const timeoutCounts = [];
        const timed = await queue.dequeue(3, 5, count => timeoutCounts.push(count));
        queue.enqueue('discarded');
        const pending = queue.dequeue(2, 1000);
        queue.clear();
        queue.enqueue('new', 'items');
        const cleared = await pending;
        // Preserve the pre-existing distinction between single-item and batch falsy input.
        queue.enqueue(0);
        const singleFalsy = await queue.dequeue();
        queue.enqueue(0, false, 'kept');
        const batchFalsy = await queue.dequeue();
        return { initial, batched, timed, timeoutCounts, cleared, singleFalsy, batchFalsy, length: queue.length };
    }
    const result = await exercise(Queue);
    assert.deepEqual(result, await exercise(OldQueue));
    assert.deepEqual(result.initial, ['first']);
    assert.deepEqual(result.batched, ['a', 'b', 'c']);
    assert.deepEqual(result.timeoutCounts, [1]);
    assert.deepEqual(result.cleared, ['new', 'items']);
    assert.equal(result.length, 0);
});

test('DOM IDs, selectors, inline handlers, and model option identifiers match HEAD', () => {
    const htmlPatterns = [
        /\bid\s*=\s*(["'])[^"']*\1/g,
        /\b(?:data-tab|onclick|onchange)\s*=\s*(["'])[^"']*\1/g,
        /<option\b[^>]*\bvalue\s*=\s*(["'])[^"']*\1/g,
        /<(?:script|link)\b[^>]*\b(?:src|href)\s*=\s*(["'])[^"']*\1/g,
    ];
    for (const pattern of htmlPatterns) assert.deepEqual(matches(current('index.html'), pattern), matches(baseline('index.html'), pattern));
    for (const path of javaScript) {
        const selector = /\b(?:getElementById|querySelector|querySelectorAll)\((?:'[^']*'|"[^"]*"|`[^`]*`)\)/g;
        assert.deepEqual(matches(current(path), selector), matches(baseline(path), selector), path);
    }
    const model = /(?:hiyori_pro_zh|natori_pro_zh|[\w.-]+\.model3\.json|ParamMouth\w+)/g;
    assert.deepEqual(matches(current('js/live2d/live2d.js').replace(/\/\*[\s\S]*?\*\//g, ''), model), matches(baseline('js/live2d/live2d.js').replace(/\/\*[\s\S]*?\*\//g, ''), model));
});

test('protocol matching literals and language-specific fallback inputs match HEAD', () => {
    const matchers = /(?:\b(?:message|response|payload)\.(?:type|state|method)\s*===\s*(['"])[^'"]*\1|\.includes\((['"])[^'"]*\2\))/g;
    for (const path of javaScript) assert.deepEqual(matches(current(path), matchers), matches(baseline(path), matchers), path);
    const protocolValues = /\b(?:type|state|method|mode|reason|transport|version|format|sample_rate|channels|frame_duration|protocolVersion)\s*:\s*(?:'[^']*'|"[^"]*"|\d+)/g;
    for (const path of javaScript) assert.deepEqual(matches(current(path), protocolValues), matches(baseline(path), protocolValues), path);
    for (const path of ['js/app.js', 'js/config/manager.js', 'js/core/mcp/tools.js', 'js/core/network/websocket.js', 'js/core/network/wakeword-bridge.js', 'js/ui/controller.js']) {
        const literals = /(['"])(?:\\.|(?!\1)[^\\\r\n])*?\1/g;
        const hanStrings = source => matches(source, literals).filter(value => /\p{Script=Han}/u.test(value));
        // Diagnostics are translated; assert each original Chinese literal that remains
        // in translated source still exists verbatim in the baseline (no new fixtures).
        const old = hanStrings(baseline(path));
        for (const literal of hanStrings(current(path))) assert.ok(old.includes(literal), `${path}: altered language data ${literal}`);
    }
    const network = current('js/core/network/websocket.js');
    for (const literal of ["text: '嘿，你好呀'", "message.text.includes('绑定')", "message.text.includes('bind')"]) {
        assert.ok(baseline('js/core/network/websocket.js').includes(literal));
        assert.ok(network.includes(literal));
    }
    for (const path of ['js/app.js', 'js/core/mcp/tools.js']) {
        const prompt = "'描述一下看到的物品'";
        assert.ok(current(path).includes(prompt) && baseline(path).includes(prompt), path);
    }
    for (const path of ['js/core/network/wakeword-bridge.js', 'js/ui/controller.js']) {
        assert.equal(matches(current(path), /'唤醒词'/g).length, matches(baseline(path), /'唤醒词'/g).length, path);
    }
    const wakeExamples = source => source.match(/<textarea\b[^>]*\bid="wakewordList"[^>]*>/)?.[0]
        .match(/placeholder="([^"]*)"/)?.[1].split('&#10;').slice(1);
    assert.deepEqual(wakeExamples(current('index.html')), wakeExamples(baseline('index.html')));
});

test('interpolation expressions and MCP schema/mock placeholders match HEAD', () => {
    // Flat interpolations include variable access, function calls, and formatted values.
    // Nested display-template branches are also reviewed via their inner interpolations.
    const expressions = source => matches(source, /\$\{[^{}]*\}/g)
        .map(value => value.replace(/(['"])(?:\\.|(?!\1)[^\\])*?\1/g, '<string>'));
    for (const path of javaScript) assert.deepEqual(expressions(current(path)), expressions(baseline(path)), path);
    assert.deepEqual(JSON.parse(current('js/config/default-mcp-tools.json')), JSON.parse(baseline('js/config/default-mcp-tools.json')));
    const replacement = /const regex = new RegExp\([^\n]+/g;
    assert.deepEqual(matches(current('js/core/mcp/tools.js'), replacement), matches(baseline('js/core/mcp/tools.js'), replacement));
});

test('CSS rules and JS class/style actions match HEAD', () => {
    assert.equal(withoutCssComments(current('css/index.css')), withoutCssComments(baseline('css/index.css')));
    const actions = /(?:\.classList\.(?:add|remove|toggle|contains)\([^\n;]*\)|\.style\.[\w]+\s*=\s*[^\n;]+)/g;
    for (const path of javaScript) assert.deepEqual(matches(current(path), actions), matches(baseline(path), actions), path);
});
