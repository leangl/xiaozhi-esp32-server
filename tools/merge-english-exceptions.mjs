#!/usr/bin/env node
// Mechanical merge of explicitly reviewed candidates, never an auto-allowlist.
// Review each candidate's meaning/scope before invoking this helper.
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const destination=path.join(root,'docs/maintenance/english-exceptions.json');
const files=process.argv.slice(2);
if(!files.length)throw Error('Provide explicit reviewed candidate JSON paths');
const manifest=JSON.parse(readFileSync(destination,'utf8'));
let added=0,removed=0;
for(const file of files){
  const raw=JSON.parse(readFileSync(file,'utf8'));
  const candidates=Array.isArray(raw)?raw:raw.exceptions;
  if(!Array.isArray(candidates))throw Error('Candidate must be an array or contain exceptions');
  for(const e of raw.remove||[]){
    if(e.kind!=='line'||!e.path||!e.hash)throw Error('Removal must identify one exact line exception');
    const index=manifest.exceptions.findIndex(x=>x.path===e.path&&x.kind===e.kind&&x.hash===e.hash);
    if(index<0)throw Error('Reviewed removal is stale or missing');
    manifest.exceptions.splice(index,1);removed++;
  }
  for(const e of candidates){
    if(!e.path||!e.category||!e.reason||!['line','file'].includes(e.kind))throw Error('Incomplete candidate');
    if(manifest.exceptions.some(x=>x.path===e.path&&x.kind==='file'))continue;
    if(manifest.exceptions.some(x=>x.path===e.path&&x.kind===e.kind&&x.hash===e.hash))continue;
    manifest.exceptions.push(e);added++;
  }
}
const json=JSON.stringify(manifest,null,2).replace(/\p{Script=Han}/gu,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'))+'\n';
writeFileSync(destination,json);
console.log(JSON.stringify({added,removed,total:manifest.exceptions.length}));
