// Compare Springdoc output from the original and translated sources.
// API prose/tags/examples may change; routes, schemas, required flags, enum
// values, defaults, security declarations and operation IDs must not change.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const [beforePath, afterPath] = process.argv.slice(2);
if (!beforePath || !afterPath) {
  throw new Error('Usage: node tools/openapi-translation-check.mjs BEFORE.json AFTER.json');
}
const before = JSON.parse(fs.readFileSync(beforePath, 'utf8'));
const after = JSON.parse(fs.readFileSync(afterPath, 'utf8'));
const keyMaps = new Set(['properties', 'schemas', 'paths', 'responses', 'content',
  'headers', 'securitySchemes', 'examples', 'requestBodies', 'encoding', 'callbacks']);
const prose = new Set(['description', 'summary', 'title', 'example', 'examples', 'tags']);

function contract(value, isKeyMap = false) {
  if (Array.isArray(value)) return value.map(item => contract(item));
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().flatMap(key => {
    if (!isKeyMap && prose.has(key)) return [];
    return [[key, contract(value[key], !isKeyMap && keyMaps.has(key))]];
  }));
}
// Guard against confusing a property named "content" or "description" with
// OpenAPI metadata; enum/default values remain contractual, not prose.
assert.deepEqual(contract({ properties: { content: { description: 'A', type: 'string' },
  description: { type: 'integer' } } }), { properties: {
  content: { type: 'string' }, description: { type: 'integer' } } });
assert.notDeepEqual(contract({ properties: { tags: { enum: ['a'], default: 'a' } } }),
  contract({ properties: { tags: { enum: ['b'], default: 'b' } } }));
assert.deepEqual(contract(after), contract(before), 'OpenAPI contract changed beyond translated metadata');

let descriptions = 0;
let localizedExamples = 0;
function inspect(value, path = []) {
  if (!value || typeof value !== 'object') return;
  for (const [key, item] of Object.entries(value)) {
    if (typeof item === 'string') {
      if (['description', 'summary', 'title'].includes(key)) {
        descriptions++;
        assert.ok(!/\p{Script=Han}/u.test(item), `Untranslated OpenAPI prose at ${[...path, key].join('/')}`);
      }
      if (key === 'example' && /\p{Script=Han}/u.test(item)) localizedExamples++;
    } else inspect(item, [...path, key]);
  }
}
inspect(after);
console.log(JSON.stringify({ paths: Object.keys(after.paths).length,
  schemas: Object.keys(after.components.schemas).length, descriptions,
  localizedExamples, contractSha256: createHash('sha256')
    .update(JSON.stringify(contract(after))).digest('hex'), result: 'pass' }, null, 2));
