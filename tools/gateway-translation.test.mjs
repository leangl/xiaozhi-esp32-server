// Offline differential tests. Never import app.js: it starts real listeners.
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash, createHmac } from 'node:crypto';
import crypto from 'node:crypto';
import { EventEmitter } from 'node:events';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const gateway = path.join(root, 'gateway');
const base = '93f026ad3a9a5572c9cf6ce651dd8fcf46fd2419';
const source = (rel, baseline = false) => baseline
    ? execFileSync('git', ['show', `${base}:${rel}`], { cwd: gateway, encoding: 'utf8' })
    : readFileSync(path.join(gateway, rel), 'utf8');
const plain = value => JSON.parse(JSON.stringify(value));

function load(rel, baseline = false) {
    const module = { exports: {} };
    let now = 1700000000000;
    class Clock extends Date { static now() { return now; } }
    const require = name => {
        if (name === 'debug') return () => () => {};
        if (name === 'dotenv') return { config() {} };
        if (name === 'events') return EventEmitter;
        if (name === 'crypto') return crypto;
        throw Error(`Unexpected dependency: ${name}`);
    };
    const context = vm.createContext({ module, exports: module.exports, require,
        Buffer, Date: Clock, console: { log() {}, warn() {}, error() {} },
        process: { env: { MQTT_SIGNATURE_KEY: 'offline-test-key', MQTT_ENDPOINT: 'mqtt.example.invalid' } } });
    new vm.Script(source(rel, baseline), { filename: rel }).runInContext(context, { timeout: 1000 });
    return { api: module.exports, advance(ms) { now += ms; } };
}

class Socket extends EventEmitter {
    writable = true;
    packets = [];
    ended = false;
    write(buffer) { this.packets.push(Buffer.from(buffer)); }
    end() { this.ended = true; }
    destroy() { this.ended = true; }
}
function protocol(baseline) {
    const { MQTTProtocol } = load('mqtt-protocol.js', baseline).api;
    const socket = new Socket();
    return { instance: new MQTTProtocol(socket, { get() { return 8192; } }), socket };
}

test('gateway JavaScript parses without running a bridge or reading live environment', () => {
    const files = execFileSync('git', ['ls-files', '-z', '*.js'], { cwd: gateway, encoding: 'utf8' }).split('\0').filter(Boolean);
    for (const file of files) execFileSync(process.execPath, ['--input-type=commonjs', '--check'], { input: source(file), stdio: ['pipe', 'pipe', 'pipe'] });
    const old = JSON.parse(source('package.json', true));
    const current = JSON.parse(source('package.json'));
    old.description = current.description = '<translated prose>';
    assert.deepEqual(current, old, 'package behavior and dependencies must remain unchanged');
});

test('MQTT remaining-length encoding and decoding match the baseline at boundaries', () => {
    for (const n of [0, 1, 127, 128, 16383, 16384, 2097151, 268435455]) {
        const old = protocol(true).instance;
        const current = protocol(false).instance;
        const a = old.encodeRemainingLength(n), b = current.encodeRemainingLength(n);
        assert.equal(b.bytesLength, a.bytesLength);
        assert.deepEqual(b.bytes, a.bytes);
        const frame = Buffer.concat([Buffer.from([0x30]), b.bytes.subarray(0, b.bytesLength)]);
        assert.deepEqual(plain(current.decodeRemainingLength(frame)), { value: n, bytesRead: b.bytesLength });
    }
});

test('MQTT publish packets, fragmented input and event fields match the baseline', () => {
    for (const qos of [0, 1]) {
        const outputs = [];
        for (const baseline of [true, false]) {
            const { instance, socket } = protocol(baseline);
            instance.isConnected = true;
            instance.sendPublish('device/test', '{"type":"hello","version":3}', qos, false, false, 23);
            const packet = socket.packets[0];
            const events = [];
            instance.on('publish', event => events.push(plain(event)));
            socket.emit('data', packet.subarray(0, 3));
            assert.equal(events.length, 0);
            socket.emit('data', packet.subarray(3));
            assert.equal(events.length, 1);
            outputs.push({ hex: packet.toString('hex'), event: events[0] });
        }
        assert.deepEqual(outputs[1], outputs[0]);
        assert.equal(outputs[1].event.qos, qos);
    }
});

test('MQTT acknowledgement, keep-alive and disconnect packets remain byte-identical', () => {
    const outputs = [];
    for (const baseline of [true, false]) {
        const { instance, socket } = protocol(baseline);
        instance.isConnected = true;
        instance.sendConnack(0, false);
        instance.sendSuback(0x1234, 0);
        instance.sendPingResp();
        const packets = socket.packets.map(p => p.toString('hex'));
        instance.parseDisconnect(Buffer.from([0xe0, 0]));
        outputs.push({ packets, ended: socket.ended, connected: instance.isConnected });
    }
    assert.deepEqual(outputs[1], outputs[0]);
    assert.deepEqual(outputs[1].packets, ['20020000', '9003123400', 'd000']);
    assert.equal(outputs[1].connected, false);
    assert.equal(outputs[1].ended, true);
});

test('MQTT credentials preserve HMAC inputs, config fields, endpoint and IP normalization', () => {
    const outputs = [];
    for (const baseline of [true, false]) {
        const api = load('utils/mqtt_config_v2.js', baseline).api;
        const config = api.generateMqttConfig('group', 'aa:bb:cc:dd:ee:ff', 'uuid', { ip: '192.0.2.1' });
        const expected = createHmac('sha256', 'offline-test-key').update(config.client_id + '|' + config.username).digest('base64');
        assert.equal(config.password, expected);
        assert.throws(() => api.validateMqttCredentials(config.client_id, config.username, 'invalid'));
        const credentials = api.validateMqttCredentials(config.client_id, config.username, config.password, '::ffff:192.0.2.2');
        assert.equal(credentials.macAddress, 'aa:bb:cc:dd:ee:ff');
        assert.equal(credentials.userData.ip, '192.0.2.2');
        outputs.push(plain({ config, credentials }));
    }
    assert.deepEqual(outputs[1], outputs[0]);
});

test('call pairing, session IDs, cleanup and timeout state match the baseline', () => {
    const outputs = [];
    for (const baseline of [true, false]) {
        const loaded = load('utils/call-manager.js', baseline);
        const manager = new loaded.api.CallManager();
        const first = manager.requestCall('AA', 'BB', 'Caller');
        const joined = manager.joinCall('BB');
        manager.setCallSessionId('AA', 'session-a');
        const active = plain(manager.getActiveCalls());
        const cleared = plain(manager.clearDevice('AA'));
        const pending = manager.requestCall('CC', 'DD', 'Second caller');
        loaded.advance(60001);
        const timedOut = plain(manager.cleanupTimeoutCalls());
        outputs.push(plain({ first, joined, active, cleared, pending, timedOut, remaining: manager.getPendingCalls() }));
    }
    assert.deepEqual(outputs[1], outputs[0]);
    assert.equal(outputs[1].joined.status, 'bridged');
    assert.equal(outputs[1].cleared.sessionId, 'session-a');
    assert.equal(outputs[1].timedOut.length, 1);
    assert.equal(outputs[1].remaining.length, 0);
});

test('UDP framing/crypto operations and HTTP route declarations are unchanged', () => {
    const select = text => text.split(/\r?\n/).filter(line => /\.(?:writeUInt\w*|readUInt\w*|createCipheriv|createDecipheriv|setAuthTag|getAuthTag|setAAD)\(|Buffer\.alloc\(|\bapp\.(?:get|post|put|delete)\(/.test(line)).map(line => line.trim().replace(/\s*\/\/.*$/, ''));
    assert.deepEqual(select(source('app.js')), select(source('app.js', true)));
    assert.equal(createHash('sha256').update(JSON.stringify(select(source('app.js')))).digest('hex').length, 64);
});
