import assert from 'node:assert/strict';
import test from 'node:test';
import { validateLock } from './build-npm-lock.mjs';

const entry = () => ({resolved: 'https://registry.npmjs.org/example/-/example-1.0.0.tgz',
  integrity: 'sha512-YWJjZA=='});
const lock = (value = entry()) => ({lockfileVersion: 3, packages: {'': {}, 'node_modules/example': value}});

test('accepts official HTTPS registry plus integrity', () => {
  assert.equal(validateLock(lock()), 1);
});
test('rejects a mirror even when package integrity exists', () => {
  assert.throws(() => validateLock(lock({...entry(), resolved: 'https://registry.npmmirror.com/example.tgz'})), /need reviewed/);
});
test('rejects suffix tricks, cleartext, alternate ports and userinfo', () => {
  for (const resolved of ['https://registry.npmjs.org.bad.test/a', 'http://registry.npmjs.org/a',
    'https://registry.npmjs.org:8443/a', 'https://secret@registry.npmjs.org/a']) {
    assert.throws(() => validateLock(lock({...entry(), resolved})), /need reviewed/);
  }
});
test('rejects query/fragment, git and local sources', () => {
  for (const resolved of ['https://registry.npmjs.org/a?token=secret',
    'https://registry.npmjs.org/a#fragment', 'git+https://example.test/a', 'file:../example']) {
    assert.throws(() => validateLock(lock({...entry(), resolved})), /need reviewed/);
  }
});
test('rejects missing/malformed integrity and missing resolution', () => {
  for (const value of [{resolved: entry().resolved}, {integrity: entry().integrity},
    {...entry(), integrity: 'sha1-YWJjZA=='}, {...entry(), integrity: 'sha512-not valid'}]) {
    assert.throws(() => validateLock(lock(value)), /need reviewed/);
  }
});
test('rejects old or missing lock format', () => {
  for (const value of [null, {}, {packages: {'': {}}}, {lockfileVersion: 1, packages: {}},
    {lockfileVersion: 4, packages: {'': {}}}, {lockfileVersion: 3, packages: []}]) {
    assert.throws(() => validateLock(value), /reviewed npm lockfile/);
  }
});
test('failure never echoes a supplied URL or secret', () => {
  assert.throws(() => validateLock(lock({...entry(), resolved: 'https://secret-token@bad.test/private'})),
    error => !error.message.includes('secret-token') && !error.message.includes('bad.test'));
});
