// Offline guard. It does not rewrite the lock or run npm lifecycle scripts.
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

export function validateLock(lock) {
  if (!lock || typeof lock !== 'object' || ![2, 3].includes(lock.lockfileVersion) || !lock.packages
    || typeof lock.packages !== 'object' || Array.isArray(lock.packages) || !('' in lock.packages)) {
    throw new Error('A reviewed npm lockfile version 2 or newer is required');
  }
  const bad = [];
  for (const [name, entry] of Object.entries(lock.packages)) {
    if (!name) continue; // root package
    let approved = false;
    try {
      const url = new URL(entry.resolved);
      approved = url.protocol === 'https:' && url.hostname === 'registry.npmjs.org'
        && !url.username && !url.password && !url.port && !url.search && !url.hash
        && /^sha(256|384|512)-[A-Za-z0-9+/]+=*$/.test(entry.integrity || '');
    } catch { /* Missing, local, git and unknown sources require separate review. */ }
    if (!approved) bad.push(name);
  }
  if (bad.length) {
    // Do not echo URLs: a malformed lock may contain credentials.
    throw new Error(`${bad.length} npm packages need reviewed official-registry URLs and integrity hashes; ask the lockfile owner to migrate/review them`);
  }
  return Object.keys(lock.packages).length - 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  let lock;
  try {
    lock = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  } catch {
    console.error('Build input rejected: missing or invalid JSON lockfile');
    process.exitCode = 1;
  }
  if (lock !== undefined) try {
    const count = validateLock(lock);
    console.log(`npm lock source check passed: ${count} packages. Operator approval of npm and lifecycle egress remains a release gate.`);
  } catch (error) {
    console.error(`Build input rejected: ${error.message}`);
    process.exitCode = 1;
  }
}
