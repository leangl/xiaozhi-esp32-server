#!/usr/bin/env node
// Read-only Java translation review against a Git revision. No compiler/dependencies.
// This is a lexer-based guard, not a Java parser or a proof of runtime equivalence.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const han = /\p{Script=Han}/u;
const operators = ['>>>=', '<<=', '>>=', '...', '>>>', '::', '->', '++', '--', '==', '!=', '<=', '>=', '&&', '||', '+=', '-=', '*=', '/=', '&=', '|=', '^=', '%=', '<<', '>>'];

// Java processes eligible Unicode escapes before recognizing comments/literals.
function unicodeSource(source) {
    let out = '', slashes = 0;
    for (let i = 0; i < source.length;) {
        if (source[i] === '\\' && slashes % 2 === 0) {
            const match = source.slice(i).match(/^\\u+([0-9a-fA-F]{4})/);
            if (match) {
                const char = String.fromCharCode(parseInt(match[1], 16));
                out += char;
                i += match[0].length;
                // An escape-produced backslash does not start another escape.
                slashes = char === '\\' ? 1 : 0;
                continue;
            }
        }
        const char = source[i++];
        out += char;
        slashes = char === '\\' ? slashes + 1 : 0;
    }
    return out;
}

export function lex(raw) {
    const source = unicodeSource(raw), tokens = [];
    let i = 0, line = 1;
    const consume = n => {
        const value = source.slice(i, i + n);
        line += (value.match(/\n/g) || []).length;
        i += n;
        return value;
    };
    while (i < source.length) {
        const rest = source.slice(i);
        const whitespace = rest.match(/^\s+/);
        if (whitespace) { consume(whitespace[0].length); continue; }
        if (rest.startsWith('//')) {
            const end = rest.indexOf('\n');
            consume(end < 0 ? rest.length : end);
            continue;
        }
        if (rest.startsWith('/*')) {
            const end = rest.indexOf('*/', 2);
            if (end < 0) throw new Error(`Unterminated comment at line ${line}`);
            consume(end + 2);
            continue;
        }
        const startLine = line;
        if (rest[0] === '"' || rest[0] === "'") {
            const block = rest.startsWith('"""'), quote = block ? '"""' : rest[0];
            let end = quote.length, closed = false;
            while (end < rest.length) {
                if (rest[end] === '\\') { end += 2; continue; }
                if (rest.startsWith(quote, end)) { end += quote.length; closed = true; break; }
                if (!block && /[\n\r]/.test(rest[end])) throw new Error(`Newline in literal at line ${startLine}`);
                end++;
            }
            if (!closed) throw new Error(`Unterminated literal at line ${startLine}`);
            tokens.push({ kind: quote === "'" ? 'char' : 'string', value: consume(end), line: startLine });
            continue;
        }
        const identifier = rest.match(/^[\p{ID_Start}_$][\p{ID_Continue}$]*/u);
        if (identifier) {
            tokens.push({ kind: 'identifier', value: consume(identifier[0].length), line: startLine });
            continue;
        }
        const number = rest.match(/^(?:0[xX](?:[\da-fA-F_]+(?:\.[\da-fA-F_]*)?|\.[\da-fA-F_]+)(?:[pP][+-]?[\d_]+)?[fFdDlL]?|0[bB][01_]+[lL]?|(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?[\d_]+)?[fFdDlL]?)/);
        if (number) {
            tokens.push({ kind: 'number', value: consume(number[0].length), line: startLine });
            continue;
        }
        const operator = operators.find(value => rest.startsWith(value)) || rest[0];
        tokens.push({ kind: 'operator', value: consume(operator.length), line: startLine });
    }
    return tokens;
}

export function placeholders(value) {
    // Preserve order, indexes, types, precision and escapes. Prose may move around them.
    return [...value.matchAll(/\$\{[^{}]+\}|\{\{[^{}]+\}\}|\{\}|\{[A-Za-z_$][\w.$:-]*\}|\{\d+(?:,[^{}]+)?\}|%(?:\d+\$)?[-#+ 0,(<]*\d*(?:\.\d+)?(?:[tT][a-zA-Z]|[a-zA-Z%])|\\(?:[btnfr"'\\]|[0-7]{1,3})/g)].map(m => m[0]);
}

const sensitiveCalls = new Set(['equals', 'equalsIgnoreCase', 'contains', 'containsKey', 'startsWith', 'endsWith', 'matches', 'split', 'replace', 'replaceAll', 'replaceFirst', 'indexOf', 'lastIndexOf', 'compile', 'get', 'put', 'remove', 'getString', 'getValue', 'getProperty', 'getParameter', 'getHeader', 'getBean', 'setProperty', 'setHeader', 'setAttribute', 'setParameter', 'addHeader', 'select', 'eq', 'ne', 'like', 'in', 'orderByAsc', 'orderByDesc', 'apply', 'last', 'forName']);
const proseAnnotations = new Set(['Schema', 'Operation', 'Parameter', 'Tag', 'ApiResponse', 'Info', 'Api', 'ApiOperation', 'ApiParam', 'DisplayName', 'LogOperation']);
const proseAttributes = new Set(['description', 'summary', 'title', 'message', 'notes']);

function contexts(tokens) {
    const result = new Map(), stack = [];
    for (let i = 0; i < tokens.length; i++) {
        const v = tokens[i].value;
        if (v === '(') {
            let start = i - 1;
            while (start > 0 && tokens[start - 1].value === '.') start -= 2;
            const name = tokens[i - 1]?.value;
            stack.push({ name, annotation: tokens[start - 1]?.value === '@', open: i });
        }
        if (tokens[i].kind === 'string') {
            const annotation = [...stack].reverse().find(s => s.annotation);
            const call = [...stack].reverse().find(s => !s.annotation);
            let attr;
            if (annotation) {
                for (let j = i - 1; j > annotation.open; j--) {
                    if (tokens[j].value === '=') { attr = tokens[j - 1]?.value; break; }
                    if (tokens[j].value === ',') break;
                }
            }
            result.set(i, { annotation: annotation?.name, attribute: attr, call: call?.name });
        }
        if (v === ')') stack.pop();
    }
    return result;
}

function stringCategory(token, context) {
    const { annotation, attribute, call } = context || {};
    if (annotation) {
        const prose = proseAttributes.has(attribute) ||
            (proseAnnotations.has(annotation) && (!attribute || (annotation === 'Tag' && attribute === 'name')));
        return prose ? 'annotation-prose' : 'annotation-contract';
    }
    if (sensitiveCalls.has(call)) return 'contract-call';
    if (/\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE\s+TABLE)\b/i.test(token.value)) return 'sql';
    if (/^(?:"|""")(?:https?:|wss?:|\/[^\s]*|[\w.-]+[._][\w.-]+)(?:"|""")$/.test(token.value)) return 'key-or-endpoint';
    if (han.test(token.value)) return 'translated-prose';
    if (['info', 'warn', 'error', 'debug', 'trace', 'println', 'printf'].includes(call)) return 'diagnostic-prose';
    return 'non-Han-string';
}

function structuralDiff(before, after) {
    const value = t => t.kind === 'string' ? '<string>' : t.kind + ':' + t.value;
    const differences = [];
    let a = 0, b = 0;
    while (a < before.length || b < after.length) {
        if (a < before.length && b < after.length && value(before[a]) === value(after[b])) { a++; b++; continue; }
        const startA = a, startB = b;
        let best;
        for (let x = 0; x <= 24 && a + x < before.length; x++) {
            for (let y = 0; y <= 24 && b + y < after.length; y++) {
                if (x + y === 0 || (best && x + y >= best[0] + best[1])) continue;
                if (value(before[a + x]) === value(after[b + y]) &&
                    value(before[a + x + 1] || { kind: '', value: '' }) === value(after[b + y + 1] || { kind: '', value: '' })) best = [x, y];
            }
        }
        if (best) { a += best[0]; b += best[1]; }
        else { a = before.length; b = after.length; }
        differences.push({ beforeLine: before[startA]?.line, afterLine: after[startB]?.line,
            before: before.slice(startA, a).map(value), after: after.slice(startB, b).map(value) });
    }
    return differences;
}

export function compare(beforeSource, afterSource) {
    const before = lex(beforeSource), after = lex(afterSource);
    const structure = structuralDiff(before, after), strings = [], placeholderChanges = [];
    const beforeStrings = before.map((t, i) => ({ ...t, index: i })).filter(t => t.kind === 'string');
    const afterStrings = after.map((t, i) => ({ ...t, index: i })).filter(t => t.kind === 'string');
    const ctx = contexts(before);
    // Pair literals only when the non-string token skeleton is identical.
    if (structure.length === 0) {
        for (let i = 0; i < beforeStrings.length; i++) {
            const a = beforeStrings[i], b = afterStrings[i];
            if (a.value === b.value) continue;
            const context = ctx.get(a.index), category = stringCategory(a, context);
            const change = { beforeLine: a.line, afterLine: b.line, category, context, before: a.value, after: b.value };
            strings.push(change);
            if (JSON.stringify(placeholders(a.value)) !== JSON.stringify(placeholders(b.value))) placeholderChanges.push(change);
        }
    }
    return { tokenCount: after.length, structure, strings, placeholderChanges };
}

const contractCategories = new Set(['annotation-contract', 'contract-call', 'sql', 'key-or-endpoint', 'non-Han-string']);
const sha256 = value => createHash('sha256').update(value, 'utf8').digest('hex');

export function reviewCandidates(candidates, entries) {
    const used = new Set(), reviewed = [], unresolved = [];
    for (const candidate of candidates) {
        const index = entries.findIndex((entry, i) => !used.has(i) &&
            entry.path === candidate.path && entry.category === candidate.category &&
            entry.beforeSha256 === sha256(candidate.before) && entry.afterSha256 === sha256(candidate.after));
        if (index < 0) unresolved.push(candidate);
        else { used.add(index); reviewed.push({ ...candidate, reason: entries[index].reason }); }
    }
    return { reviewed, unresolved, stale: entries.filter((_, i) => !used.has(i)) };
}

function selfTest() {
    const same = (a, b) => assert.equal(compare(a, b).structure.length, 0);
    same('int x=1; // old', '/* new */ int x = 1;');
    same('log.info("你好 {} %2$s", x);', 'log.info("Hello {} %2$s", x);');
    same('String x="https://x/*literal*/";', 'String x="https://x/*literal*/";');
    assert.ok(compare('int oldName(){return 1;}', 'int newName(){return 1;}').structure.length);
    assert.ok(compare('int x=1001;', 'int x=1002;').structure.length);
    assert.ok(compare('boolean x=a&&b;', 'boolean x=a||b;').structure.length);
    assert.ok(compare("char x='中';", "char x='E';").structure.length);
    assert.equal(compare('log.info("你好 {}", x);', 'log.info("Hello %s", x);').placeholderChanges.length, 1);
    assert.equal(compare('@GetMapping("/old") void x(){}', '@GetMapping("/new") void x(){}').strings[0].category, 'annotation-contract');
    assert.equal(compare('@Schema(description="名称") int x;', '@Schema(description="Name") int x;').strings[0].category, 'annotation-prose');
    assert.equal(compare('x.equals("失败");', 'x.equals("Failure");').strings[0].category, 'contract-call');
    assert.equal(compare('Pattern.compile("中文|测试");', 'Pattern.compile("English|test");').strings[0].category, 'contract-call');
    assert.equal(lex('String s="""\n// text\n""";').filter(t => t.kind === 'string').length, 1);
    same('int x=1; \\u002f\\u002f comment', 'int x=1;');
    assert.deepEqual(placeholders('"{{name}} ${key} {0,number} %02d %1$tF \\n"'), ['{{name}}', '${key}', '{0,number}', '%02d', '%1$tF', '\\n']);
    assert.deepEqual(placeholders('"History: {history_memory} Conversation: {conversation}"'), ['{history_memory}', '{conversation}']);
    assert.equal(compare('String s="对话 {conversation}";', 'String s="Conversation {dialogue}";').placeholderChanges.length, 1);
    const candidate = { path: 'Example.java', category: 'contract-call', before: '"旧文案"', after: '"New prose"' };
    const entry = { path: candidate.path, category: candidate.category, beforeSha256: sha256(candidate.before), afterSha256: sha256(candidate.after), reason: 'Test fixture' };
    assert.equal(reviewCandidates([candidate], [entry]).reviewed.length, 1);
    assert.equal(reviewCandidates([{ ...candidate, after: '"Changed again"' }], [entry]).unresolved.length, 1);
    assert.equal(reviewCandidates([], [entry]).stale.length, 1);
    assert.equal(reviewCandidates([candidate, candidate], [entry]).unresolved.length, 1);
    console.log('21 lexer, contract, placeholder, mutation and stale-review checks passed');
}

function main() {
    const args = process.argv.slice(2);
    if (args.includes('--self-test')) { selfTest(); return; }
    const baseIndex = args.indexOf('--base'), base = baseIndex < 0 ? 'HEAD' : args[baseIndex + 1];
    if (!base || base.startsWith('-')) throw new Error('Expected revision after --base');
    const git = (...params) => execFileSync('git', params, { cwd: root, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
    const baselineCommit = git('rev-parse', '--verify', base + '^{commit}').trim();
    const paths = git('diff', '--name-only', '-z', baselineCommit, '--', '*.java').split('\0').filter(Boolean).sort();
    const results = [], digest = createHash('sha256');
    for (const path of paths) {
        try {
            const before = git('show', `${baselineCommit}:${path}`), after = readFileSync(resolve(root, path), 'utf8');
            digest.update(path + '\0' + after + '\0');
            const result = compare(before, after);
            if (result.structure.length || result.strings.length || result.placeholderChanges.length) results.push({ path, ...result });
        } catch (error) { results.push({ path, error: error.message }); }
    }
    const candidates = results.flatMap(result => (result.strings || []).filter(s => contractCategories.has(s.category)).map(s => ({ path: result.path, ...s })));
    const reviewPath = resolve(root, 'docs/maintenance/java-contract-review.json');
    const manifest = existsSync(reviewPath) ? JSON.parse(readFileSync(reviewPath, 'utf8')) : { entries: [] };
    if (manifest.version !== undefined && manifest.version !== 1) throw new Error('Unsupported contract-review version');
    if (manifest.baselineCommit && manifest.baselineCommit !== baselineCommit) throw new Error('Contract reviews refer to a different baseline commit');
    for (const entry of manifest.entries) {
        if (!entry.path || !entry.reason || !contractCategories.has(entry.category) ||
            !/^[a-f0-9]{64}$/.test(entry.beforeSha256) || !/^[a-f0-9]{64}$/.test(entry.afterSha256)) throw new Error('Invalid contract review entry');
    }
    const reviews = reviewCandidates(candidates, manifest.entries);
    const summary = { baselineCommit, javaFiles: paths.length, snapshotSha256: digest.digest('hex'),
        structuralFiles: results.filter(r => r.error || r.structure.length).length,
        changedStrings: results.reduce((n, r) => n + (r.strings?.length || 0), 0),
        placeholderChanges: results.reduce((n, r) => n + (r.placeholderChanges?.length || 0), 0),
        contractCandidates: candidates.length, reviewedCandidates: reviews.reviewed.length,
        unresolved: reviews.unresolved.length, staleReviews: reviews.stale.length };
    console.log(JSON.stringify(args.includes('--summary') ? summary : { summary, results, unresolved: reviews.unresolved, staleReviews: reviews.stale }, null, 2));
    // Only exact reviewed pairs pass. Structural/placeholder failures bypass reviews.
    if (summary.structuralFiles || summary.placeholderChanges || summary.unresolved || summary.staleReviews) process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
