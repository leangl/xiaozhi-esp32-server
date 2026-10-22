#!/usr/bin/env node
// A content inventory is not a translation-quality certificate. Residual prose
// remains pending until reviewed; never turn the baseline into an allowlist.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'docs/maintenance');
const han = /\p{Script=Han}/u;
const sha = data => createHash('sha256').update(data).digest('hex');
const generated = new Set(['docs/maintenance/english-inventory.json']);
const tracked = () => execFileSync('git', ['ls-files','--cached','--others','--exclude-standard','-z'], {cwd:root,encoding:'utf8'})
  .split('\0').filter(p=>p && !generated.has(p));
const protectedPath = p => p.startsWith('main/manager-api/src/main/resources/db/changelog/') ||
  /^main\/manager-(web|mobile)\/src\/i18n\/zh_(CN|TW)\.(js|ts)$/.test(p) ||
  /^main\/manager-api\/src\/main\/resources\/i18n\/(messages|validation)(?:_zh_(CN|TW))?\.properties$/.test(p);
function inventory() {
  const files=[];
  for(const p of tracked()) {
    const file=path.join(root,p); if(!existsSync(file))continue;
    const data=readFileSync(file);
    const binary=data.includes(0)||/\.(png|jpg|jpeg|gif|webp|ico|woff2?|ttf|onnx|pt|mp3|wav|ogg|pdf|zip)$/i.test(p);
    const lines=binary?[]:data.toString('utf8').split(/\r?\n/)
      .flatMap((text,index)=>han.test(text)?[{line:index+1,text,hash:sha(text)}]:[]);
    const module=p.startsWith('main/')?p.split('/').slice(0,2).join('/'):p.includes('/')?p.split('/')[0]:'root';
    files.push({path:p,module,binary,chinesePath:han.test(p),protected:protectedPath(p),chineseLines:lines});
  }
  return {sourceCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),files};
}
function summary(data) {
  const modules={};
  for(const f of data.files){const m=modules[f.module]??={files:0,chineseFiles:0,chineseLines:0,binaryAssets:0};
    m.files++;if(f.chineseLines.length)m.chineseFiles++;m.chineseLines+=f.chineseLines.length;if(f.binary)m.binaryAssets++;}
  return modules;
}
function write(name,data){mkdirSync(out,{recursive:true});writeFileSync(path.join(out,name),JSON.stringify(data,null,2)+'\n');}
function publicInventory(data) {
  return {...data,files:data.files.map(f=>({...f,chineseLines:f.chineseLines.map(({line,hash})=>({line,hash}))}))};
}
function exemptionFor(file,line,exceptions) {
  return exceptions.find(e=>e.path===file.path && (e.kind==='file' || e.hash===line.hash));
}
function unreviewedLines(files,exceptions) {
  return files.flatMap(file=>file.chineseLines.filter(line=>!exemptionFor(file,line,exceptions))
    .map(line=>({path:file.path,line:line.line,hash:line.hash})));
}
const command=process.argv[2]||'scan';
if(command==='baseline'){
  const dest=path.join(out,'english-baseline.json');
  if(existsSync(dest))throw Error('Baseline already exists; refusing to overwrite original evidence');
  const data=inventory();const hashes={};
  for(const p of tracked().filter(protectedPath))hashes[p]=sha(readFileSync(path.join(root,p)));
  write('english-baseline.json',{sourceCommit:data.sourceCommit,protectedHashes:hashes,modules:summary(data)});
  write('english-inventory.json',publicInventory(data));
  console.log(JSON.stringify({protectedFiles:Object.keys(hashes).length,modules:summary(data)},null,2));
}else if(command==='check-protected'){
  const baseline=JSON.parse(readFileSync(path.join(out,'english-baseline.json'),'utf8'));
  const failures=Object.entries(baseline.protectedHashes).filter(([p,h])=>!existsSync(path.join(root,p))||sha(readFileSync(path.join(root,p)))!==h).map(([p])=>p);
  console.log(JSON.stringify({checked:Object.keys(baseline.protectedHashes).length,failures},null,2));
  if(failures.length)process.exitCode=1;
}else if(command==='scan'){
  const data=inventory();write('english-inventory.json',publicInventory(data));console.log(JSON.stringify(summary(data),null,2));
}else if(command==='check'){
  const data=inventory();
  const manifest=JSON.parse(readFileSync(path.join(out,'english-exceptions.json'),'utf8'));
  const exceptions=manifest.exceptions;
  const used=new Set(),failures=[],unreviewed=unreviewedLines(data.files,exceptions);
  for(const e of exceptions) {
    if(!e.path||!e.reason||!e.category||!['file','line'].includes(e.kind)||/[?*]/.test(e.path)||path.isAbsolute(e.path)||e.path.split('/').includes('..'))throw Error('Invalid or blanket exception');
    if(e.kind==='file'&&!e.sha256)throw Error('Whole-file exceptions require an exact content hash');
    if(e.companion&&!existsSync(path.join(root,e.companion)))failures.push({path:e.path,error:'Missing English companion'});
    if(e.kind==='file'&&(!existsSync(path.join(root,e.path))||sha(readFileSync(path.join(root,e.path)))!==e.sha256))failures.push({path:e.path,error:'Stale file exception'});
  }
  for(const file of data.files){
    for(const line of file.chineseLines){
      const e=exemptionFor(file,line,exceptions);
      if(e)used.add(e);
    }
    if(file.chinesePath) {
      const e=exceptions.find(e=>e.path===file.path&&e.allowChinesePath);
      if(e)used.add(e); else failures.push({path:file.path,error:'Unreviewed Chinese path'});
    }
  }
  for(const e of exceptions)if(!used.has(e))failures.push({path:e.path,error:'Unused exception'});
  write('english-inventory.json',publicInventory(data));
  console.log(JSON.stringify({unreviewedLines:unreviewed.length,exceptionErrors:failures.length,failures,firstUnreviewed:unreviewed.slice(0,30)},null,2));
  if(unreviewed.length||failures.length)process.exitCode=1;
}else if(command==='self-test'){
  const file={path:'example.js'}, line={hash:'original'};
  const e={kind:'line',path:'example.js',hash:'original',category:'locale',reason:'Fixture'};
  assert.equal(exemptionFor(file,line,[e]),e);
  assert.equal(exemptionFor(file,{hash:'changed'},[e]),undefined);
  assert.equal(exemptionFor({path:'other.js'},line,[e]),undefined);
  assert.equal(han.test('English technical comment'),false);
  assert.equal(han.test(String.fromCodePoint(0x4e2d)),true);
  const localeText=String.fromCodePoint(0x4e2d,0x6587);
  const locale={path:'locale.js',chineseLines:[{line:1,hash:sha(localeText)}]};
  const reviewed={path:'locale.js',kind:'line',hash:sha(localeText),category:'locale',reason:'Retained locale value'};
  assert.equal(unreviewedLines([locale],[reviewed]).length,0);
  const addedComment={line:2,hash:sha('// '+localeText+' technical comment')};
  assert.equal(unreviewedLines([{...locale,chineseLines:[...locale.chineseLines,addedComment]}],[reviewed]).length,1);
  assert.equal(unreviewedLines([{...locale,chineseLines:[{line:1,hash:sha(localeText+' changed')}]}],[reviewed]).length,1);
  console.log('PASS: retained locale fixture passes; new Han technical comment and changed fixture fail; exact path/hash and stale-line checks pass');
}else{
  throw Error('Usage: node tools/english-audit.mjs baseline|scan|check-protected|check|self-test');
}
