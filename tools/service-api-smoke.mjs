#!/usr/bin/env node
/**
 * Bounded real-HTTP smoke against ONE explicitly labelled disposable candidate.
 * No compose startup, .env/config reads, package installation, OCR, controller
 * mocks, host DB access, log scraping, real users or external API destinations.
 *
 * Main workflow (this tool NEVER launches/restarts/removes containers):
 * 1. Launch the approved isolated images with fresh volumes; all services need
 *    com.docker.compose.project=xiaozhi-policy-rehearsal and
 *    xiaozhi.validation=service-policy-rehearsal-20261021. Enable renren.redis.open.
 *    Publish candidate Nginx 8002 on 127.0.0.1:18002, not Java's internal 8003.
 *    Shared-network-namespace port ownership is followed and label-checked.
 * 2. Wait for the real schema and forward service-policy migration to complete.
 * 3. Pass ALL target options explicitly (no default project/container/database):
 *    node tools/service-api-smoke.mjs --seed-fixtures \
 *      --project xiaozhi-policy-rehearsal --port 18002 \
 *      --manager-container CANDIDATE_MANAGER --redis-container CANDIDATE_REDIS \
 *      --db-container CANDIDATE_MYSQL --database CANDIDATE_SCHEMA
 * 4. Launch main's loopback fake AI at :19200; then use the same target options
 *    with --run instead of --seed-fixtures and additionally:
 *      --sm-crypto-path /private/tmp/xiaozhi-policy-web.qlJKdH/main/manager-web/node_modules/sm-crypto
 *    No voice/WS/gateway configuration is read or changed by this client.
 *    Successful owner scenarios leave synthetic device IDs 02:00:00:00:00:01
 *    (owner_a, manual bind) and 02:00:00:00:00:02 (owner_b, OTA activation bind)
 *    for main's subsequent voice tests. SQL seeding alone does not bind devices.
 *    For internal:true networks without host publication, append BOTH
 *    --internal-network --http-container xiaozhi-policy-rehearsal-fake-ai-1
 *    to seed/run. This verifies declared loopback PortBindings, one internal
 *    backend network, and fake-ai's exact base image/manager namespace, then
 *    executes Python stdlib HTTP to literal 127.0.0.1:8002 in that namespace.
 * --verify-history repeats only ownership reads/rejections on the exact two
 * synthetic users/history rows already created by this tool. It requires the
 * same candidate/fixture guards, never logs their tokens, and cannot seed or
 * resume registration. The normal --run freshness gate is unchanged.
 * --verify-summary additionally exercises the internal title/summary routes
 * with the known synthetic service secret, verifies saved memory as the owner,
 * and restores the fixture's no-memory selection. Only its exact marked model
 * row may be reused after a failed fixture attempt; real configuration is never read.
 *
 * --self-test --sm-crypto-path PATH is completely offline (no Docker or HTTP).
 * Seed and run both require a fresh DB (run permits the fixture, not users).
 * A run is deliberately one-shot: synthetic accounts are random and not saved;
 * keep candidate evidence or recreate the isolated volumes in the main workflow.
 * MySQL authentication uses ONLY MYSQL_ROOT_PASSWORD inside the checked candidate
 * container, never a host credential or command-line password. Docker uses the
 * local /var/run/docker.sock only (no inherited remote context). Redis is candidate
 * DB 0 with no auth; an incompatible candidate fails closed, no fallback.
 *
 * Output contains fixed scenario names and numeric counters only. Captchas,
 * passwords, tokens, DB credentials, URLs, IDs, text and audio are never printed.
 */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { randomBytes, randomUUID } from 'node:crypto';
import { readFile, realpath } from 'node:fs/promises';
import http from 'node:http';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PROJECT = 'xiaozhi-policy-rehearsal';
const LABEL = 'service-policy-rehearsal-20261021';
const MARKER = `${LABEL}-v1`;
const IMAGE = 'xiaozhi-policy/manager:20261021';
const HTTP_IMAGE = 'xiaozhi-policy/server-base:20261021';
const ORIGIN = 'http://127.0.0.1:18002';
const INTERNAL_ORIGIN = 'http://127.0.0.1:8002';
const PREFIX = '/xiaozhi';
const BODY_LIMIT = 256 * 1024;
const HTTP_LIMIT = 120;
const DEADLINE_MS = 5 * 60 * 1000;
const SQL_FIXTURE = new URL('./service-api-fixtures.sql', import.meta.url);
const MODEL_IDS = Object.freeze({
  ASR: 'SMOKE_ASR_OPENAI', LLM: 'SMOKE_LLM_OPENAI', VLLM: 'SMOKE_VLLM_OPENAI',
  TTS: 'SMOKE_TTS_OPENAI', VAD: 'VAD_SileroVAD', Memory: 'SMOKE_MEMORY_NONE', Intent: 'SMOKE_INTENT_NONE',
});
const POLICY_MESSAGE = /^ASR configuration is unavailable; select a supported provider with a reviewed endpoint$/;
const OWNERSHIP_MESSAGE = /^(No permission to view this agent's chat history|No permission to access this agent's snapshots)$/;
const SILENCE = Buffer.from([0xf8, 0xff, 0xfe]); // Synthetic Opus silence, no microphone.
const VOICE_DEVICE_IDS = Object.freeze(['02:00:00:00:00:01', '02:00:00:00:00:02']);

// Stdin and captured stdout are bounded JSON wire data, never user-visible
// logs. No headers/bodies in argv; -I ignores Python environment hooks.
// HTTPConnection uses the literal destination, no proxy or redirect following.
const INTERNAL_HTTP = String.raw`
import base64, http.client, json, re, sys
try:
    limit = 262144
    wire = sys.stdin.buffer.read(limit * 2 + 1)
    if len(wire) > limit * 2: raise ValueError()
    request = json.loads(wire)
    if set(request) != {'method', 'path', 'headers', 'body'}: raise ValueError()
    method, path = request['method'], request['path']
    if method not in ('GET', 'POST', 'PUT', 'DELETE'): raise ValueError()
    if not isinstance(path, str) or not re.fullmatch(r'/xiaozhi/[a-zA-Z0-9_/?=&:.-]*', path): raise ValueError()
    if '..' in path or path.startswith('//'): raise ValueError()
    headers = request['headers']
    allowed = {'Accept', 'Authorization', 'Content-Type', 'Content-Length', 'Device-Id', 'Client-Id', 'User-Agent'}
    if not isinstance(headers, dict) or not set(headers).issubset(allowed): raise ValueError()
    if any(not isinstance(v, str) or '\r' in v or '\n' in v for v in headers.values()): raise ValueError()
    data = None if request['body'] is None else base64.b64decode(request['body'], validate=True)
    if data is not None and len(data) > limit: raise ValueError()
    conn = http.client.HTTPConnection('127.0.0.1', 8002, timeout=8)
    conn.request(method, path, body=data, headers=headers)
    reply = conn.getresponse()
    body = reply.read(limit + 1)
    if len(body) > limit: raise ValueError()
    result = {'status': reply.status, 'type': reply.getheader('Content-Type', ''),
              'body': base64.b64encode(body).decode('ascii')}
    conn.close()
    sys.stdout.write(json.dumps(result, separators=(',', ':')))
except BaseException:
    sys.exit(70)
`;

class CheckFailure extends Error {}
class GuardFailure extends Error {}
const check = (condition) => { if (!condition) throw new CheckFailure(); };
const guard = (condition) => { if (!condition) throw new GuardFailure(); };

function parseArgs(argv) {
  const flags = new Set(['--run', '--seed-fixtures', '--verify-history', '--verify-summary', '--self-test', '--help', '--internal-network']);
  const values = new Set(['--project', '--port', '--manager-container', '--redis-container',
    '--db-container', '--database', '--sm-crypto-path', '--http-container']);
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    guard((flags.has(key) || values.has(key)) && !(key in args));
    args[key] = flags.has(key) ? true : argv[++i];
    guard(args[key] !== undefined && (flags.has(key) || !args[key].startsWith('--')));
  }
  if (args['--help']) { guard(argv.length === 1); return args; }
  guard(['--run', '--seed-fixtures', '--verify-history', '--verify-summary', '--self-test'].filter(k => args[k]).length === 1);
  if (args['--self-test']) {
    guard(Object.keys(args).every(k => ['--self-test', '--sm-crypto-path'].includes(k)));
  } else {
    guard(args['--project'] === PROJECT && args['--port'] === '18002');
    for (const key of ['--manager-container', '--redis-container', '--db-container']) {
      guard(typeof args[key] === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$/.test(args[key]));
    }
    guard(new Set(['--manager-container', '--redis-container', '--db-container'].map(k => args[k])).size === 3);
    guard(typeof args['--database'] === 'string' && /^[a-zA-Z][a-zA-Z0-9_]{0,63}$/.test(args['--database']));
    guard(Boolean(args['--internal-network']) === Boolean(args['--http-container']));
    if (args['--internal-network']) {
      guard(/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$/.test(args['--http-container']));
      guard(!['--manager-container', '--redis-container', '--db-container'].some(k => args[k] === args['--http-container']));
    }
  }
  if (args['--run'] || args['--self-test']) guard(path.isAbsolute(args['--sm-crypto-path'] ?? ''));
  return args;
}

function validateContainer(info) {
  guard(info && /^[a-f0-9]{64}$/.test(info.id) && info.running === true);
  guard(info.labels?.['com.docker.compose.project'] === PROJECT);
  guard(info.labels?.['xiaozhi.validation'] === LABEL);
  guard(info.networkMode !== 'host');
  return info;
}

function validatePort(info, internal = false) {
  const ports = (internal ? info.bindings : info.ports)?.['8002/tcp'];
  guard(Array.isArray(ports) && ports.length > 0);
  guard(ports.some(p => p.HostIp === '127.0.0.1' && p.HostPort === '18002'));
  // Refuse accidental public/alternate publication of the API as well.
  guard(ports.every(p => p.HostIp === '127.0.0.1' && p.HostPort === '18002'));
}

function validateNetwork(info) {
  guard(info && /^[a-f0-9]{64}$/.test(info.id));
  guard(info.name === `${PROJECT}_backend` && info.internal === true && info.driver === 'bridge');
  guard(info.labels?.['com.docker.compose.project'] === PROJECT);
  guard(info.labels?.['com.docker.compose.network'] === 'backend');
}

function validateAttachment(info, networkId) {
  const networks = Object.values(info.networks ?? {});
  guard(networks.length === 1 && networks[0].NetworkID === networkId);
  guard(info.networkMode === `${PROJECT}_backend`);
}

function validateHttpContainer(info, managerId, imageId) {
  guard(info.labels?.['com.docker.compose.service'] === 'fake-ai');
  guard(info.image === HTTP_IMAGE && info.imageId === imageId);
  guard(info.networkMode === `container:${managerId}`);
  guard(Object.keys(info.networks ?? {}).length === 0);
  guard(Object.keys(info.bindings ?? {}).length === 0);
}

function boundedPath(endpoint, internal = false) {
  guard(typeof endpoint === 'string' && /^\/[a-zA-Z0-9_/?=&:.-]*$/.test(endpoint));
  guard(!endpoint.startsWith('//') && !endpoint.includes('..'));
  const origin = internal ? INTERNAL_ORIGIN : ORIGIN;
  const url = new URL(PREFIX + endpoint, origin);
  guard(url.origin === origin && url.hostname === '127.0.0.1' && url.port === (internal ? '8002' : '18002'));
  guard(url.pathname.startsWith(`${PREFIX}/`));
  return url;
}

// No shell interpolation is used for host commands. Stdout/stderr are bounded,
// captured, and never inherited, printed or attached to a thrown error.
function command(argv, input = '', maxBytes = BODY_LIMIT) {
  return new Promise((resolve, reject) => {
    const child = spawn('docker', ['--host', 'unix:///var/run/docker.sock', ...argv],
      { stdio: ['pipe', 'pipe', 'pipe'] });
    const chunks = [];
    let size = 0;
    let failed = false;
    const timer = setTimeout(() => { failed = true; child.kill('SIGKILL'); }, 10_000);
    const consume = (chunk, keep) => {
      size += chunk.length;
      if (size > maxBytes) { failed = true; child.kill('SIGKILL'); }
      else if (keep) chunks.push(chunk);
    };
    child.stdout.on('data', c => consume(c, true));
    child.stderr.on('data', c => consume(c, false));
    child.on('error', () => { clearTimeout(timer); reject(new GuardFailure()); });
    child.stdin.on('error', () => {});
    child.on('close', code => {
      clearTimeout(timer);
      if (code !== 0 || failed) reject(new GuardFailure());
      else resolve(Buffer.concat(chunks).toString('utf8').trim());
    });
    child.stdin.end(input);
  });
}

class Candidate {
  constructor(args) { this.args = args; this.ids = {}; this.started = Date.now(); this.requests = 0; }
  // Docker metadata/exec round trips add latency, but both modes remain bounded.
  budget() { guard(Date.now() - this.started < DEADLINE_MS * (this.args['--internal-network'] ? 2 : 1)); }
  async inspect(target) {
    this.budget();
    // Deliberately never inspect .Config.Env or print whole inspect records.
    const format = '{"id":{{json .Id}},"labels":{{json .Config.Labels}},"running":{{json .State.Running}},'
      + '"image":{{json .Config.Image}},"imageId":{{json .Image}},"networkMode":{{json .HostConfig.NetworkMode}},'
      + '"ports":{{json .NetworkSettings.Ports}},"bindings":{{json .HostConfig.PortBindings}},"networks":{{json .NetworkSettings.Networks}}}';
    return validateContainer(JSON.parse(await command(['inspect', '--type', 'container', '--format', format, target])));
  }
  async pin() {
    for (const role of ['manager', 'redis', 'db']) {
      const info = await this.inspect(this.args[`--${role}-container`]);
      this.ids[role] = info.id;
    }
    guard(new Set(Object.values(this.ids)).size === 3);
    if (this.args['--internal-network']) {
      const manager = await this.roleGuard('manager');
      guard(manager.labels?.['com.docker.compose.service'] === 'manager');
      const networks = Object.values(manager.networks ?? {});
      guard(networks.length === 1 && /^[a-f0-9]{64}$/.test(networks[0].NetworkID));
      this.networkId = networks[0].NetworkID;
      const httpContainer = await this.inspect(this.args['--http-container']);
      this.httpImageId = JSON.parse(await command(['image', 'inspect', '--format', '{{json .Id}}', HTTP_IMAGE]));
      guard(/^sha256:[a-f0-9]{64}$/.test(this.httpImageId));
      validateHttpContainer(httpContainer, this.ids.manager, this.httpImageId);
      this.ids.http = httpContainer.id;
      guard(new Set(Object.values(this.ids)).size === 4);
      for (const role of ['manager', 'db', 'redis']) await this.roleGuard(role);
    }
    await this.apiGuard();
  }
  async roleGuard(role) {
    this.budget();
    guard(this.ids[role]);
    const info = await this.inspect(this.ids[role]);
    guard(info.id === this.ids[role]);
    if (this.networkId && role !== 'http') {
      guard(info.labels?.['com.docker.compose.service'] === role);
      validateAttachment(info, this.networkId);
    }
    return info;
  }
  async apiGuard() {
    let info = await this.roleGuard('manager');
    guard(info.image === IMAGE);
    if (this.args['--internal-network']) {
      validatePort(info, true);
      const format = '{"id":{{json .Id}},"name":{{json .Name}},"internal":{{json .Internal}},'
        + '"driver":{{json .Driver}},"labels":{{json .Labels}}}';
      const network = JSON.parse(await command(['network', 'inspect', '--format', format, this.networkId]));
      validateNetwork(network);
      guard(network.id === this.networkId);
      validateHttpContainer(await this.roleGuard('http'), this.ids.manager, this.httpImageId);
      return;
    }
    const visited = new Set([info.id]);
    for (let i = 0; info.networkMode?.startsWith('container:'); i++) {
      guard(i < 3);
      info = await this.inspect(info.networkMode.slice('container:'.length));
      guard(!visited.has(info.id));
      visited.add(info.id);
    }
    validatePort(info);
  }
  async sql(statement) {
    await this.roleGuard('db'); // Recheck pinned labels immediately before EVERY DB access.
    // Fixed in-container shell only; statement travels on stdin, not argv.
    // MYSQL_ROOT_PASSWORD belongs to this fresh candidate, not the host.
    return command(['exec', '-i', this.ids.db, 'sh', '-c',
      'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --no-defaults --protocol=socket --user=root --batch --skip-column-names --raw --default-character-set=utf8mb4 --database="$1"',
      'synthetic-api-smoke', this.args['--database']], statement);
  }
  async redis(argv, input = '') {
    await this.roleGuard('redis'); // No redis discovery, SCAN, KEYS or fallback DB.
    return command(['exec', '-i', this.ids.redis, 'redis-cli', '--raw', '-n', '0', ...argv], input);
  }
  async fresh() {
    const output = await this.sql('SELECT (SELECT COUNT(*) FROM sys_user),'
      + '(SELECT COUNT(*) FROM sys_user_token),(SELECT COUNT(*) FROM ai_agent),'
      + '(SELECT COUNT(*) FROM ai_device),(SELECT COUNT(*) FROM ai_agent_chat_history),'
      + '(SELECT COUNT(*) FROM ai_agent_chat_audio),(SELECT COUNT(*) FROM ai_agent_snapshot);');
    guard(output === '0\t0\t0\t0\t0\t0\t0');
  }
  async fixtureGuard() {
    guard(await this.sql("SELECT param_value FROM sys_params WHERE param_code='validation.api_smoke_fixture';") === MARKER);
    guard(await this.sql("SELECT COUNT(*) FROM ai_agent_template WHERE id='SMOKE_APPROVED_TEMPLATE' AND sort=0;") === '1');
  }
  async request(method, endpoint, { token, body, binary = false, deviceId } = {}) {
    await this.apiGuard();
    guard(++this.requests <= HTTP_LIMIT);
    const url = boundedPath(endpoint, Boolean(this.args['--internal-network']));
    const payload = body === undefined ? null : Buffer.from(JSON.stringify(body));
    guard(!payload || payload.length <= BODY_LIMIT);
    // Browser requests always have this header; login's client fingerprint path
    // currently assumes it is non-null, after persisting the token.
    const headers = { Accept: binary ? '*/*' : 'application/json', 'User-Agent': 'xiaozhi-policy-synthetic-smoke/1' };
    if (deviceId) {
      guard(method === 'POST' && endpoint === '/ota/'
        && (VOICE_DEVICE_IDS.includes(deviceId) || /^02:53(:[a-f0-9]{2}){4}$/.test(deviceId)));
      headers['Device-Id'] = deviceId;
      headers['Client-Id'] = deviceId;
    }
    if (token) headers.Authorization = `Bearer ${token}`;
    if (payload) { headers['Content-Type'] = 'application/json'; headers['Content-Length'] = String(payload.length); }
    let response;
    if (this.args['--internal-network']) {
      const wire = JSON.stringify({ method, path: url.pathname + url.search, headers,
        body: payload ? payload.toString('base64') : null });
      guard(Buffer.byteLength(wire) <= BODY_LIMIT * 2);
      const reply = JSON.parse(await command(['exec', '-i', this.ids.http, 'python3', '-I', '-c', INTERNAL_HTTP], wire, BODY_LIMIT * 2));
      guard(Number.isInteger(reply.status) && reply.status >= 100 && reply.status <= 599
        && typeof reply.type === 'string' && typeof reply.body === 'string'
        && /^[a-zA-Z0-9+/]*={0,2}$/.test(reply.body));
      response = { status: reply.status, type: reply.type, bytes: Buffer.from(reply.body, 'base64') };
      guard(response.bytes.length <= BODY_LIMIT);
    } else response = await new Promise((resolve, reject) => {
      // Node http goes directly to the numeric loopback, with no environment
      // proxy support and no redirect following (including on auth endpoints).
      const req = http.request(url, { method, headers, agent: false }, res => {
        const chunks = []; let length = 0;
        res.on('data', c => {
          length += c.length;
          if (length > BODY_LIMIT) res.destroy(new GuardFailure()); else chunks.push(c);
        });
        res.on('error', () => reject(new GuardFailure()));
        res.on('end', () => resolve({ status: res.statusCode, type: res.headers['content-type'] ?? '',
          bytes: Buffer.concat(chunks) }));
      });
      const timer = setTimeout(() => req.destroy(new GuardFailure()), 8_000);
      req.on('close', () => clearTimeout(timer));
      req.on('error', () => reject(new GuardFailure()));
      req.end(payload);
    });
    guard(response.status < 300 || response.status >= 400);
    lastHTTP.status = response.status;
    lastHTTP.code = -1;
    if (binary) return response;
    guard(response.type.includes('application/json'));
    const envelope = JSON.parse(response.bytes.toString('utf8'));
    guard(envelope && typeof envelope === 'object' && Number.isInteger(envelope.code));
    lastHTTP.code = envelope.code;
    return { status: response.status, envelope };
  }
  async ok(method, endpoint, options) {
    const r = await this.request(method, endpoint, options);
    if (!(r.status >= 200 && r.status < 300 && r.envelope.code === 0)) {
      process.stdout.write(`REJECTED status=${Number(r.status)} code=${Number(r.envelope.code)}\n`);
    }
    check(r.status >= 200 && r.status < 300 && r.envelope.code === 0);
    return r.envelope.data;
  }
}

function denied(response, codes, message) {
  check(response.status >= 200 && response.status < 500);
  check(response.envelope.code !== 0 && (codes.includes(response.envelope.code)
    || (response.envelope.code === 500 && message?.test(response.envelope.msg))));
}
function policyDenied(response) { denied(response, [], POLICY_MESSAGE); }
function ownerDenied(response) { denied(response, [401, 403, 10169, 10132], OWNERSHIP_MESSAGE); }
function sqlString(value) { return `CONVERT(X'${Buffer.from(value, 'utf8').toString('hex')}' USING utf8mb4)`; }
function opaqueId(id) { check(typeof id === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(id)); return id; }
function safeFields(value, allowed) {
  check(value && typeof value === 'object' && !Array.isArray(value));
  check(Object.keys(value).every(k => allowed.includes(k)));
}

async function loadCrypto(modulePath) {
  guard(path.isAbsolute(modulePath ?? ''));
  const root = await realpath(modulePath);
  guard(path.basename(root) === 'sm-crypto');
  const manifest = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
  guard(manifest.name === 'sm-crypto');
  const sm2 = createRequire(import.meta.url)(root).sm2;
  guard(typeof sm2?.doEncrypt === 'function');
  return sm2;
}

const counters = { passed: 0, failed: 0 };
const lastHTTP = { status: 0, code: -1 };
let activeScenario = 'arguments';
async function scenario(name, fn, required = false) {
  activeScenario = name;
  try { await fn(); counters.passed++; process.stdout.write(`PASS ${name}\n`); }
  catch (error) {
    if (!(error instanceof CheckFailure)) throw error;
    counters.failed++; process.stdout.write(`FAIL ${name} step=${activeScenario}\n`);
    process.stdout.write(`COUNTERS http_status=${lastHTTP.status} api_code=${lastHTTP.code}\n`);
    if (required) throw new GuardFailure();
  }
}

async function seed(candidate) {
  // Prove fixed-target transport readiness before any candidate fixture writes.
  await candidate.ok('GET', '/user/pub-config');
  await candidate.fresh();
  guard(await candidate.sql("SELECT COUNT(*) FROM sys_params WHERE param_code='validation.api_smoke_fixture';") === '0');
  guard(await candidate.sql("SELECT COUNT(*) FROM ai_model_config WHERE id='VAD_SileroVAD' "
    + "AND is_enabled=1 AND JSON_UNQUOTE(JSON_EXTRACT(config_json,'$.type'))='silero';") === '1');
  // Read only this source-controlled fixture, never a caller-selected SQL path.
  await candidate.sql(await readFile(SQL_FIXTURE, 'utf8'));
  await candidate.redis(['DEL', 'sys:params', 'server:config', 'model:data:VAD_SileroVAD', 'model:name:VAD_SileroVAD']);
  await candidate.fixtureGuard();
}

async function captcha(candidate) {
  const id = randomUUID();
  const image = await candidate.request('GET', `/user/captcha?uuid=${id}`, { binary: true });
  check(image.status === 200 && image.type.startsWith('image/') && image.bytes.length > 0);
  // The HTTP endpoint produces the code; fixture reads that exact UUID from the
  // labelled Redis. Never replace a code, OCR it, dump Redis, or patch validation.
  const raw = await candidate.redis(['GET', `sys:captcha:${id}`]);
  let code;
  try { code = JSON.parse(raw); } catch { throw new GuardFailure(); }
  guard(typeof code === 'string' && /^[a-zA-Z0-9]{5}$/.test(code));
  return { id, code };
}

async function activationCode(candidate, mac) {
  // Real OTA HTTP creates its own candidate Redis activation fixture. Do not
  // synthesize Redis serializer metadata or call the incompatible /device/register
  // legacy captcha route. Ignore returned WS/MQTT metadata; never connect to it.
  const response = await candidate.request('POST', '/ota/', { binary: true, deviceId: mac, body: {
    version: 1, mac_address: mac, application: { name: 'synthetic-smoke', version: '0.0.0-smoke' },
    board: { type: 'synthetic-smoke', mac },
  } });
  check(response.status === 200 && response.type.includes('application/json'));
  const ota = JSON.parse(response.bytes.toString('utf8'));
  check(!ota.error && typeof ota.activation?.code === 'string' && /^[0-9]{6}$/.test(ota.activation.code));
  return ota.activation.code;
}

async function historyIdentity(candidate, user) {
  // Only identifiers from this run's synthetic assistant/session, no text/audio.
  const identity = await candidate.sql('SELECT CAST(id AS CHAR),audio_id FROM ai_agent_chat_history '
    + `WHERE agent_id=${sqlString(user.agent)} AND session_id=${sqlString(user.session)} ORDER BY id;`);
  check(/^[0-9]+\t[a-zA-Z0-9_-]+$/.test(identity));
  return identity;
}

async function historyOwnership(candidate, a, b) {
  ownerDenied(await candidate.request('GET', `/agent/${a.agent}/sessions?page=1&limit=5`, { token: b.token }));
  ownerDenied(await candidate.request('GET', `/agent/${a.agent}/chat-history/${a.session}`, { token: b.token }));
  ownerDenied(await candidate.request('GET', `/agent/${a.agent}/chat-history/user`, { token: b.token }));
  ownerDenied(await candidate.request('GET', `/agent/${a.audio}/chat-history/audio`, { token: b.token }));
  ownerDenied(await candidate.request('POST', `/agent/audio/${a.audio}`, { token: b.token }));
  ownerDenied(await candidate.request('POST', `/agent/chat-history/getDownloadUrl/${a.agent}/${a.session}`, { token: b.token }));
  ownerDenied(await candidate.request('POST', `/agent/chat-title/${a.session}/generate`, { token: b.token }));
  ownerDenied(await candidate.request('POST', `/agent/chat-summary/${a.session}/save`, { token: b.token }));
  const mixed = await candidate.ok('GET', `/agent/${b.agent}/chat-history/${a.session}`, { token: b.token });
  check(Array.isArray(mixed) && mixed.length === 0);
  const ownerText = await candidate.ok('GET', `/agent/${a.audio}/chat-history/audio`, { token: a.token });
  check(ownerText === a.content);
}

async function verifyExistingHistory(candidate) {
  await candidate.fixtureGuard();
  const content = 'Synthetic API smoke history';
  const rows = (await candidate.sql('SELECT u.username,t.token,a.id,h.session_id,h.audio_id '
    + 'FROM sys_user u JOIN sys_user_token t ON t.user_id=u.id '
    + 'JOIN ai_agent a ON a.user_id=u.id JOIN ai_agent_chat_history h ON h.agent_id=a.id '
    + "WHERE u.super_admin=0 AND u.username REGEXP '^smoke_[0-9a-f]{12}_owner_[ab]$' "
    + `AND h.content=${sqlString(content)} AND h.chat_type=1 ORDER BY u.username;`)).split('\n');
  guard(rows.length === 2);
  const users = rows.map((row, index) => {
    const fields = row.split('\t');
    guard(fields.length === 5);
    const [username, token, agent, session, audio] = fields;
    guard(new RegExp(`^smoke_[0-9a-f]{12}_owner_${index === 0 ? 'a' : 'b'}$`).test(username));
    guard(/^[A-Za-z0-9_-]{16,256}$/.test(token));
    return { username, token, agent: opaqueId(agent), session: opaqueId(session), audio: opaqueId(audio), content };
  });
  guard(users[0].username.slice(0, 18) === users[1].username.slice(0, 18));
  await scenario('history_audio_ownership_replay', () => historyOwnership(candidate, ...users));
  return users;
}

async function verifyExistingSummary(candidate) {
  const [a] = await verifyExistingHistory(candidate);
  await scenario('owner_summary_and_title_persistence', async () => {
    const count = await candidate.sql("SELECT COUNT(*) FROM ai_model_config WHERE id='SMOKE_MEMORY_SHORT';");
    guard(count === '0' || count === '1');
    if (count === '0') await candidate.sql('INSERT INTO ai_model_config '
        + '(id,model_type,model_code,model_name,is_default,is_enabled,config_json,sort,remark) VALUES '
        + "('SMOKE_MEMORY_SHORT','Memory','mem_local_short','Synthetic summary',0,1,"
        + "JSON_OBJECT('type','mem_local_short','llm','SMOKE_LLM_OPENAI'),0,'Synthetic only');");
    guard(await candidate.sql("SELECT COUNT(*) FROM ai_model_config WHERE id='SMOKE_MEMORY_SHORT' "
      + "AND model_type='Memory' AND is_enabled=1 AND remark='Synthetic only' "
      + "AND JSON_UNQUOTE(JSON_EXTRACT(config_json,'$.type'))='mem_local_short' "
      + "AND JSON_UNQUOTE(JSON_EXTRACT(config_json,'$.llm'))='SMOKE_LLM_OPENAI';") === '1');
    await candidate.ok('PUT', `/agent/${a.agent}`, { token: a.token, body: { memModelId: 'SMOKE_MEMORY_SHORT' } });
    // These are server-to-server routes, not ordinary-user operations.
    await candidate.ok('POST', `/agent/chat-title/${a.session}/generate`, { token: 'a'.repeat(64) });
    check(await candidate.sql('SELECT COUNT(*) FROM ai_agent_chat_title '
      + `WHERE session_id=${sqlString(a.session)} AND title='Synthetic title';`) === '1');
    await candidate.ok('POST', `/agent/chat-summary/${a.session}/save`, { token: 'a'.repeat(64) });
    let saved = false;
    for (let attempt = 0; attempt < 8; attempt++) {
      saved = await candidate.sql('SELECT COUNT(*) FROM ai_agent '
        + `WHERE id=${sqlString(a.agent)} AND summary_memory='Synthetic memory summary';`) === '1';
      if (saved) break;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    check(saved);
    const owner = await candidate.ok('GET', `/agent/${a.agent}`, { token: a.token });
    check(owner.summaryMemory === 'Synthetic memory summary');
    // Future voice trials keep the no-memory contract selected by the base fixture.
    await candidate.ok('PUT', `/agent/${a.agent}`, { token: a.token, body: { memModelId: MODEL_IDS.Memory } });
  });
}

async function run(candidate, sm2) {
  await candidate.fresh();
  await candidate.fixtureGuard();
  let publicKey;
  await scenario('pub_config', async () => {
    const config = await candidate.ok('GET', '/user/pub-config');
    safeFields(config, ['enableMobileRegister', 'version', 'year', 'allowUserRegister', 'mobileAreaList',
      'beianIcpNum', 'beianGaNum', 'name', 'sm2PublicKey', 'systemWebMenu']);
    check(config.enableMobileRegister === false && config.allowUserRegister === true);
    check(typeof config.sm2PublicKey === 'string' && /^(04)?[a-fA-F0-9]{128}$/.test(config.sm2PublicKey));
    publicKey = config.sm2PublicKey;
  }, true);

  const nonce = randomBytes(6).toString('hex');
  const users = [];
  for (const [index, role] of ['admin', 'owner_a', 'owner_b'].entries()) {
    const username = `smoke_${nonce}_${role}`;
    const password = `Sm0ke!${randomBytes(20).toString('hex')}`;
    let token;
    await scenario(`register_login_${role}`, async () => {
      for (const endpoint of ['/user/register', '/user/login']) {
        activeScenario = `${endpoint === '/user/register' ? 'register' : 'login'}_${role}`;
        const cap = await captcha(candidate);
        const encrypted = '04' + sm2.doEncrypt(cap.code + password, publicKey, 1);
        const data = await candidate.ok('POST', endpoint, { body: { username, password: encrypted, captchaId: cap.id } });
        check(await candidate.redis(['EXISTS', `sys:captcha:${cap.id}`]) === '0');
        if (endpoint === '/user/login') {
          check(typeof data?.token === 'string' && data.token.length >= 16);
          token = data.token;
        }
      }
      activeScenario = `user_info_${role}`;
      const info = await candidate.ok('GET', '/user/info', { token });
      check(info.username === username && info.superAdmin === (index === 0 ? 1 : 0));
    }, true);
    users.push({ token, username, role });
  }
  const [admin, a, b] = users;
  await scenario('normal_role_admin_rejection', async () => {
    denied(await candidate.request('GET', '/models/list?modelType=ASR&page=1&limit=5', { token: a.token }), [403]);
  });
  await scenario('unauthenticated_selector_rejection', async () => {
    denied(await candidate.request('GET', '/models/names?modelType=ASR'), [401, 10020, 10021]);
  });
  for (const user of [a, b]) {
    await scenario(`selectors_${user.role}`, async () => {
      for (const [type, expected] of Object.entries(MODEL_IDS)) {
        const rows = await candidate.ok('GET', `/models/names?modelType=${type}`, { token: user.token });
        check(Array.isArray(rows) && rows.some(row => row.id === expected));
        for (const row of rows) safeFields(row, ['id', 'modelName']);
        check(rows.every(row => row.id !== 'SMOKE_REMOVED_ASR'));
      }
      const llms = await candidate.ok('GET', '/models/llm/names', { token: user.token });
      check(Array.isArray(llms) && llms.some(row => row.id === MODEL_IDS.LLM && row.type === 'openai'));
      for (const row of llms) safeFields(row, ['id', 'modelName', 'type']);
      const voices = await candidate.ok('GET', `/models/${MODEL_IDS.TTS}/voices`, { token: user.token });
      check(Array.isArray(voices) && voices.some(row => row.id === 'SMOKE_VOICE_ALLOY'));
      for (const row of voices) {
        safeFields(row, ['id', 'name', 'voiceDemo', 'languages', 'isClone']);
        check(row.isClone !== true);
        check(row.voiceDemo == null || (typeof row.voiceDemo === 'string'
          && !row.voiceDemo.includes('local-only') && !/[?&#]/.test(row.voiceDemo)));
      }
    });
  }
  await scenario('removed_sms_rejection', async () => {
    denied(await candidate.request('POST', '/user/smsVerification', { body: {
      phone: '00000000000', captchaId: randomUUID(), captcha: 'AAAAA',
    } }), [10068]);
    denied(await candidate.request('PUT', '/user/retrieve-password', { body: {} }), [10073]);
  });
  await scenario('removed_provider_rejection', async () => {
    policyDenied(await candidate.request('POST', '/models/ASR/funasr', { token: admin.token, body: {
      id: 'SMOKE_REJECTED_ADD', modelCode: 'SyntheticRemoved', modelName: 'Synthetic removed',
      isEnabled: 1, isDefault: 0, configJson: { type: 'funasr', base_url: 'http://127.0.0.1:19200' },
    } }));
    policyDenied(await candidate.request('PUT', '/models/enable/SMOKE_REMOVED_ASR/1', { token: admin.token }));
    policyDenied(await candidate.request('PUT', '/models/default/SMOKE_REMOVED_ASR', { token: admin.token }));
    guard(await candidate.sql("SELECT COUNT(*) FROM ai_model_config WHERE id='SMOKE_REJECTED_ADD' "
      + "OR (id='SMOKE_REMOVED_ASR' AND (is_enabled<>0 OR is_default<>0));") === '0');
  });

  for (const [i, user] of [a, b].entries()) {
    await scenario(`assistant_device_${user.role}`, async () => {
      const templates = await candidate.ok('GET', '/agent/template', { token: user.token });
      check(Array.isArray(templates) && templates[0]?.id === 'SMOKE_APPROVED_TEMPLATE');
      user.agent = opaqueId(await candidate.ok('POST', '/agent', { token: user.token,
        body: { agentName: `Synthetic ${user.role}` } }));
      const detail = await candidate.ok('GET', `/agent/${user.agent}`, { token: user.token });
      check(detail.asrModelId === MODEL_IDS.ASR && detail.llmModelId === MODEL_IDS.LLM
        && detail.ttsModelId === MODEL_IDS.TTS && detail.ttsVoiceId === 'SMOKE_VOICE_ALLOY'
        && detail.memModelId === MODEL_IDS.Memory && detail.intentModelId === MODEL_IDS.Intent);
      // Explicitly clear the built-in music plugin; the fake AI needs no tools.
      await candidate.ok('PUT', `/agent/${user.agent}`, { token: user.token,
        body: { functions: [], chatHistoryConf: 2 } });
      user.mac = VOICE_DEVICE_IDS[i];
      if (i === 0) {
        await candidate.ok('POST', '/device/manual-add', { token: user.token, body: {
          agentId: user.agent, macAddress: user.mac, board: 'synthetic-smoke', appVersion: '0.0.0-smoke',
        } });
      } else {
        const code = await activationCode(candidate, user.mac);
        await candidate.ok('POST', `/device/bind/${user.agent}/${code}`, { token: user.token });
      }
      const devices = await candidate.ok('GET', `/device/bind/${user.agent}`, { token: user.token });
      check(Array.isArray(devices) && devices.length === 1
        && devices[0].macAddress === user.mac && devices[0].id === user.mac);
      user.device = devices[0].id;
    }, true);
  }
  await scenario('assistant_ownership', async () => {
    ownerDenied(await candidate.request('GET', `/agent/${a.agent}`, { token: b.token }));
    ownerDenied(await candidate.request('PUT', `/agent/${a.agent}`, { token: b.token, body: { agentName: 'Synthetic forbidden' } }));
    const detail = await candidate.ok('GET', `/agent/${a.agent}`, { token: a.token });
    check(detail.agentName === 'Synthetic owner_a');
    const mine = await candidate.ok('GET', '/agent/list', { token: b.token });
    check(Array.isArray(mine) && mine.some(row => row.id === b.agent) && mine.every(row => row.id !== a.agent));
  });
  await scenario('device_visibility_ownership', async () => {
    const devices = await candidate.ok('GET', `/device/bind/${a.agent}`, { token: b.token });
    check(Array.isArray(devices) && devices.length === 0);
    // The API's nonexistence error is code 500 with a fixed message, not a 5xx.
    denied(await candidate.request('PUT', `/device/update/${a.device}`, { token: b.token,
      body: { alias: 'Synthetic forbidden' } }), [], /^Device does not exist$/);
  });

  for (const user of [a, b]) {
    await scenario(`history_report_${user.role}`, async () => {
      user.session = randomUUID();
      user.content = 'Synthetic API smoke history';
      check(await candidate.ok('POST', '/agent/chat-history/report', { token: 'a'.repeat(64), body: {
        macAddress: user.mac, sessionId: user.session, chatType: 1,
        content: user.content, audioBase64: SILENCE.toString('base64'), reportTime: Date.now(),
      } }) === true);
      const rows = await candidate.ok('GET', `/agent/${user.agent}/chat-history/${user.session}`, { token: user.token });
      check(Array.isArray(rows) && rows.length === 1 && rows[0].content === user.content);
      user.audio = opaqueId(rows[0].audioId);
      user.historyIdentity = await historyIdentity(candidate, user);
      const sessions = await candidate.ok('GET', `/agent/${user.agent}/sessions?page=1&limit=5`, { token: user.token });
      check(sessions?.list?.some(row => row.sessionId === user.session));
    }, true);
  }
  await scenario('history_audio_ownership', () => historyOwnership(candidate, a, b));
  await scenario('audio_one_time_playback', async () => {
    const play = opaqueId(await candidate.ok('POST', `/agent/audio/${a.audio}`, { token: a.token }));
    const audio = await candidate.request('GET', `/agent/play/${play}`, { binary: true });
    check(audio.status === 200 && audio.bytes.equals(SILENCE));
    check((await candidate.request('GET', `/agent/play/${play}`, { binary: true })).status === 404);
  });
  await scenario('removed_assistant_selection', async () => {
    policyDenied(await candidate.request('PUT', `/agent/${a.agent}`, { token: a.token, body: { asrModelId: 'SMOKE_REMOVED_ASR' } }));
    check((await candidate.ok('GET', `/agent/${a.agent}`, { token: a.token })).asrModelId === MODEL_IDS.ASR);
    // Rejection must not delete/rekey an existing history/audio record.
    const rows = await candidate.ok('GET', `/agent/${a.agent}/chat-history/${a.session}`, { token: a.token });
    check(rows.length === 1 && rows[0].audioId === a.audio);
    check(await historyIdentity(candidate, a) === a.historyIdentity);
  });
  await scenario('removed_snapshot_restore', async () => {
    const page = await candidate.ok('GET', `/agent/${a.agent}/snapshots?page=1&limit=5`, { token: a.token });
    check(page?.list?.length > 0);
    const original = opaqueId(page.list[0].id);
    const preview = await candidate.ok('GET', `/agent/${a.agent}/snapshots/${original}`, { token: a.token });
    check(typeof preview.currentStateToken === 'string' && preview.currentStateToken.length > 0);
    const historical = randomBytes(16).toString('hex');
    // Only a newly created synthetic assistant's snapshot is copied. Existing
    // history/audio/snapshot IDs stay untouched; source-controlled policy row is
    // the only unavailable selection introduced into this historical fixture.
    await candidate.sql('INSERT INTO ai_agent_snapshot '
      + '(id,agent_id,user_id,version_no,snapshot_data,changed_fields,source,redaction_version) '
      + `SELECT ${sqlString(historical)},agent_id,user_id,version_no+1,`
      + "JSON_SET(snapshot_data,'$.asrModelId','SMOKE_REMOVED_ASR'),JSON_ARRAY('asrModelId'),'config',2 "
      + `FROM ai_agent_snapshot WHERE id=${sqlString(original)} AND agent_id=${sqlString(a.agent)};`);
    ownerDenied(await candidate.request('GET', `/agent/${a.agent}/snapshots/${historical}`, { token: b.token }));
    const oldPreview = await candidate.ok('GET', `/agent/${a.agent}/snapshots/${historical}`, { token: a.token });
    policyDenied(await candidate.request('POST', `/agent/${a.agent}/snapshots/${historical}/restore`, {
      token: a.token, body: { currentStateToken: oldPreview.currentStateToken },
    }));
    check((await candidate.ok('GET', `/agent/${a.agent}`, { token: a.token })).asrModelId === MODEL_IDS.ASR);
    const rows = await candidate.ok('GET', `/agent/${a.agent}/chat-history/${a.session}`, { token: a.token });
    check(rows.length === 1 && rows[0].audioId === a.audio);
    check(await historyIdentity(candidate, a) === a.historyIdentity);
  });
  // Denials must preserve data and leave a valid activation code usable by its owner.
  await scenario('cross_user_manual_binding_rejection', async () => {
    const mac = `02:53:${nonce.slice(6, 8)}:${nonce.slice(8, 10)}:${nonce.slice(10, 12)}:ff`;
    ownerDenied(await candidate.request('POST', '/device/manual-add', { token: b.token, body: {
      agentId: a.agent, macAddress: mac,
      board: 'synthetic-forbidden', appVersion: '0.0.0-smoke',
    } }));
    check((await candidate.sql(`SELECT COUNT(*) FROM ai_device WHERE id=${sqlString(mac)};`)).trim() === '0');
    await candidate.ok('POST', '/device/manual-add', { token: a.token, body: {
      agentId: a.agent, macAddress: mac, board: 'synthetic-owned', appVersion: '0.0.0-smoke',
    } });
  });
  await scenario('cross_user_activation_binding_rejection', async () => {
    const mac = `02:53:${nonce.slice(6, 8)}:${nonce.slice(8, 10)}:${nonce.slice(10, 12)}:fe`;
    const code = await activationCode(candidate, mac);
    ownerDenied(await candidate.request('POST', `/device/bind/${a.agent}/${code}`, { token: b.token }));
    check((await candidate.sql(`SELECT COUNT(*) FROM ai_device WHERE id=${sqlString(mac)};`)).trim() === '0');
    await candidate.ok('POST', `/device/bind/${a.agent}/${code}`, { token: a.token });
    check((await candidate.sql('SELECT COUNT(*) FROM ai_device d JOIN ai_agent g '
      + `ON d.agent_id=g.id AND d.user_id=g.user_id WHERE d.id=${sqlString(mac)} `
      + `AND g.id=${sqlString(a.agent)};`)).trim() === '1');
  });
}

async function selfTest(args) {
  await scenario('offline_argument_guards', async () => {
    const base = ['--run', '--project', PROJECT, '--port', '18002', '--manager-container', 'candidate-manager',
      '--redis-container', 'candidate-redis', '--db-container', 'candidate-db', '--database', 'candidate',
      '--sm-crypto-path', args['--sm-crypto-path']];
    assert.equal(parseArgs(base)['--project'], PROJECT);
    assert.equal(parseArgs(base.map(v => v === '--run' ? '--verify-history' : v))['--verify-history'], true);
    assert.equal(parseArgs(base.map(v => v === '--run' ? '--verify-summary' : v))['--verify-summary'], true);
    assert.equal(parseArgs([...base, '--internal-network', '--http-container', 'candidate-fake'])['--internal-network'], true);
    for (const bad of [[], ['--run'], [...base, '--api-url', ORIGIN], [...base, '--run'], [...base, '--verify-history'],
      base.map(v => v === PROJECT ? 'existing-project' : v),
      base.map(v => v === '18002' ? '8002' : v), base.map(v => v === 'candidate' ? 'db;DROP' : v),
      [...base, '--internal-network'], [...base, '--http-container', 'candidate-fake'],
      [...base, '--internal-network', '--http-container', 'candidate-manager']]) {
      assert.throws(() => parseArgs(bad), GuardFailure);
    }
  });
  await scenario('offline_internal_network_guards', async () => {
    const id = 'b'.repeat(64), manager = 'a'.repeat(64), imageId = 'sha256:' + 'c'.repeat(64);
    const network = { id, name: `${PROJECT}_backend`, internal: true, driver: 'bridge',
      labels: { 'com.docker.compose.project': PROJECT, 'com.docker.compose.network': 'backend' } };
    validateNetwork(network);
    for (const change of [{ internal: false }, { driver: 'host' }, { name: 'other' }, { labels: {} }])
      assert.throws(() => validateNetwork({ ...network, ...change }), GuardFailure);
    const owner = { networkMode: `${PROJECT}_backend`, networks: { backend: { NetworkID: id } },
      ports: {}, bindings: { '8002/tcp': [{ HostIp: '127.0.0.1', HostPort: '18002' }] } };
    validateAttachment(owner, id); validatePort(owner, true);
    assert.throws(() => validatePort(owner), GuardFailure);
    assert.throws(() => validateAttachment({ ...owner, networks: { ...owner.networks, other: { NetworkID: 'd'.repeat(64) } } }, id), GuardFailure);
    const fake = { labels: { 'com.docker.compose.service': 'fake-ai' }, image: HTTP_IMAGE,
      imageId, networkMode: `container:${manager}`, networks: {}, bindings: {} };
    validateHttpContainer(fake, manager, imageId);
    for (const change of [{ image: IMAGE }, { imageId: 'sha256:' + 'e'.repeat(64) },
      { networkMode: 'host' }, { labels: {} }, { networks: owner.networks }, { bindings: owner.bindings }])
      assert.throws(() => validateHttpContainer({ ...fake, ...change }, manager, imageId), GuardFailure);
    assert.equal(boundedPath('/user/pub-config', true).href, INTERNAL_ORIGIN + PREFIX + '/user/pub-config');
  });
  await scenario('offline_container_guards', async () => {
    const info = { id: 'a'.repeat(64), running: true, networkMode: 'candidate_default',
      labels: { 'com.docker.compose.project': PROJECT, 'xiaozhi.validation': LABEL },
      ports: { '8002/tcp': [{ HostIp: '127.0.0.1', HostPort: '18002' }] } };
    validateContainer(info); validatePort(info);
    for (const change of [{ running: false }, { labels: {} }, { networkMode: 'host' },
      { labels: { ...info.labels, 'com.docker.compose.project': 'other' } },
      { labels: { ...info.labels, 'xiaozhi.validation': 'other' } }]) {
      assert.throws(() => validateContainer({ ...info, ...change }), GuardFailure);
    }
    for (const ports of [{}, { '8003/tcp': info.ports['8002/tcp'] },
      { '8002/tcp': [{ HostIp: '0.0.0.0', HostPort: '18002' }] },
      { '8002/tcp': [{ HostIp: '127.0.0.1', HostPort: '8002' }] }]) {
      assert.throws(() => validatePort({ ...info, ports }), GuardFailure);
    }
  });
  await scenario('offline_target_and_denial_guards', async () => {
    assert.equal(boundedPath('/user/pub-config').href, ORIGIN + PREFIX + '/user/pub-config');
    for (const bad of ['http://example.test/', '//example.test/', '/../../', '/user/%2e%2e/', '/user/\\evil']) {
      assert.throws(() => boundedPath(bad), GuardFailure);
    }
    policyDenied({ status: 200, envelope: { code: 500, msg: 'ASR configuration is unavailable; select a supported provider with a reviewed endpoint' } });
    for (const r of [{ status: 500, envelope: { code: 500, msg: 'failure' } },
      { status: 200, envelope: { code: 500, msg: 'failure' } },
      { status: 200, envelope: { code: 0, msg: 'success' } }]) {
      assert.throws(() => policyDenied(r), CheckFailure);
    }
    assert.throws(() => safeFields({ id: 'x', api_key: 'x' }, ['id']), CheckFailure);
    assert.throws(() => opaqueId('../x'), CheckFailure);
    assert.equal(sqlString("'"), "CONVERT(X'27' USING utf8mb4)");
  });
  await scenario('offline_sm2_client_contract', async () => {
    const sm2 = await loadCrypto(args['--sm-crypto-path']);
    const pair = sm2.generateKeyPairHex();
    const plaintext = 'ABCDE' + 'Synthetic!9password';
    const ciphertext = '04' + sm2.doEncrypt(plaintext, pair.publicKey, 1);
    check(sm2.doDecrypt(ciphertext.slice(2), pair.privateKey, 1) === plaintext);
  });
  await scenario('offline_synthetic_fixture_contract', async () => {
    assert.deepEqual(VOICE_DEVICE_IDS, ['02:00:00:00:00:01', '02:00:00:00:00:02']);
    const sql = await readFile(SQL_FIXTURE, 'utf8');
    for (const literal of [MARKER, ...Object.values(MODEL_IDS), 'SMOKE_APPROVED_TEMPLATE',
      'models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx',
      'http://127.0.0.1:19200/v1/audio/transcriptions', 'http://127.0.0.1:19200/v1/audio/speech',
      "'smoke-asr'", "'smoke-llm'", "'smoke-tts'", "'local-only'", "'alloy'", "'wav'"])
      check(sql.includes(literal));
    check(!/INSERT INTO\s+(sys_user|ai_agent_chat_history|ai_agent_chat_audio)\b/i.test(sql));
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args['--help']) {
    process.stdout.write('Usage: see source header for explicit candidate options and seed/run sequence.\n');
    return;
  }
  if (args['--self-test']) await selfTest(args);
  else {
    activeScenario = 'candidate_guards';
    const candidate = new Candidate(args);
    await candidate.pin();
    if (args['--seed-fixtures']) await scenario('seed_synthetic_fixtures', () => seed(candidate), true);
    else if (args['--verify-history']) await verifyExistingHistory(candidate);
    else if (args['--verify-summary']) await verifyExistingSummary(candidate);
    else await run(candidate, await loadCrypto(args['--sm-crypto-path']));
    process.stdout.write(`COUNTERS http_requests=${candidate.requests}\n`);
  }
  process.stdout.write(`SUMMARY passed=${counters.passed} failed=${counters.failed}\n`);
  if (counters.failed) process.exitCode = 1;
}

// A terminal handler intentionally suppresses stack/message/cause/child output.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => {
    process.stderr.write(`FATAL ${activeScenario} redacted=1\n`);
    process.stderr.write(`SUMMARY passed=${counters.passed} failed=${counters.failed} fatal=1\n`);
    process.exitCode = 1;
  });
}
