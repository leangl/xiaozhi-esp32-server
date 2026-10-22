#!/usr/bin/env node
/**
 * Synthetic integrated MQTT -> gateway -> managed voice -> fake AI -> UDP smoke.
 *
 * Main seeds/binds 02:00:00:00:00:02, verifies project/service labels, starts the
 * candidate and loopback protocol fakes, and supplies the network namespace.
 * This client neither starts nor inspects containers, reads configuration/.env,
 * seeds devices, installs dependencies, nor calls providers directly.
 *
 * Run in a fresh Node container with --network container:<candidate-manager>,
 * the public tool mounted read-only at /tools/service-mqtt-smoke.mjs, and the
 * complete libopus-wasm package mounted read-only at /deps/libopus-wasm:
 *   node /tools/service-mqtt-smoke.mjs --candidate \
 *     --opus-module /deps/libopus-wasm/dist/index.js
 * For observed rehearsal only, --ports-output /audit-out/mqtt-client-port.json
 * publishes the exact ephemeral UDP destination to the candidate audit volume.
 * No wildcard port range is required by the observer.
 * Offline (no sockets, containers, or providers): replace --candidate with --offline.
 *
 * Namespace must belong to project xiaozhi-policy-rehearsal with label
 * xiaozhi.validation=service-policy-rehearsal-20261021. The client's fixed
 * loopback ports work inside that namespace; no host-published port is needed.
 * Main supplies gateway/voice shared SERVER_SECRET='a'.repeat(64), and gateway
 * MQTT_SIGNATURE_KEY='synthetic-rehearsal-signature-only'. No secrets are read.
 *
 * Matches tools/service-voice-smoke.py: 20 non-silent, 960-sample Opus packets
 * at 16 kHz; manual listen with ping barrier; exact STT/subtitle text; ordered
 * TTS start/sentence/stop; decoded, non-silent 60 ms output packets. Client
 * observations do not independently prove fake HTTP counts or egress isolation.
 * Only fixed labels/counters are printed, never payloads, keys, URLs, or errors.
 */

import net from 'node:net';
import dgram from 'node:dgram';
import crypto from 'node:crypto';
import path from 'node:path';
import { writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const PROJECT = 'xiaozhi-policy-rehearsal';
const LABEL = 'service-policy-rehearsal-20261021';
const DEVICE = '02:00:00:00:00:02';
const UUID = '00000000-0000-4000-8000-000000000002';
const SIGNATURE_KEY = 'synthetic-rehearsal-signature-only';
const HOST = '127.0.0.1';
const MQTT_PORT = 18883;
const UDP_PORT = 18884;
const PUBLISH_TOPIC = 'device-server';
const REPLY_TOPIC = 'devices/p2p/02_00_00_00_00_02';
const AUDIO = Object.freeze({ format: 'opus', sample_rate: 16000, channels: 1, frame_duration: 60 });
const FRAME_COUNT = 20;
const FRAME_SAMPLES = 960;
const ASR_TEXT = 'Synthetic voice smoke turn';
const SPOKEN_REPLY = 'Synthetic response complete';
const MAX_BODY = 1024 * 1024;

class SmokeFailure extends Error {}
function requireThat(condition, event) { if (!condition) throw new SmokeFailure(event); }
function bump(counts, key, n = 1) { counts[key] = (counts[key] || 0) + n; }

function argumentsFor(argv) {
    const options = { mode: null, timeout: 45, opusModule: null };
    for (let index = 0; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--help') return { help: true };
        if (arg === '--offline' || arg === '--candidate') {
            requireThat(options.mode === null, 'one_mode_required');
            options.mode = arg.slice(2);
        } else if (arg === '--opus-module') {
            options.opusModule = argv[++index];
        } else if (arg === '--ports-output') {
            options.portsOutput = argv[++index];
        } else if (arg === '--timeout') {
            const value = argv[++index];
            requireThat(/^[0-9]+$/.test(value || ''), 'invalid_timeout');
            options.timeout = Number(value);
        } else throw new SmokeFailure('unsupported_argument');
    }
    requireThat(['offline', 'candidate'].includes(options.mode), 'one_mode_required');
    requireThat(!options.portsOutput || (options.mode === 'candidate' &&
        options.portsOutput === '/audit-out/mqtt-client-port.json'), 'invalid_ports_output');
    requireThat(options.timeout >= 10 && options.timeout <= 120, 'invalid_timeout');
    requireThat(typeof options.opusModule === 'string' && path.isAbsolute(options.opusModule) &&
        options.opusModule.endsWith('/libopus-wasm/dist/index.js') &&
        !options.opusModule.split(path.sep).some(part => ['.env', 'data', 'keys'].includes(part)), 'explicit_opus_module_required');
    return options;
}

function credentials() {
    const clientId = `GID_rehearsal@@@${DEVICE.replaceAll(':', '_')}@@@${UUID}`;
    const username = Buffer.from(JSON.stringify({ ip: HOST, fixture: LABEL })).toString('base64');
    const password = crypto.createHmac('sha256', SIGNATURE_KEY).update(`${clientId}|${username}`).digest('base64');
    return { clientId, username, password };
}

function mqttString(text) {
    const value = Buffer.from(text);
    requireThat(value.length <= 65535, 'mqtt_string_limit');
    const prefix = Buffer.alloc(2); prefix.writeUInt16BE(value.length);
    return Buffer.concat([prefix, value]);
}

function mqttPacket(header, body = Buffer.alloc(0)) {
    requireThat(body.length <= MAX_BODY, 'mqtt_packet_limit');
    const length = [];
    let remaining = body.length;
    do {
        let byte = remaining % 128;
        remaining = Math.floor(remaining / 128);
        if (remaining) byte |= 128;
        length.push(byte);
    } while (remaining);
    return Buffer.concat([Buffer.from([header, ...length]), body]);
}

class MqttParser {
    constructor(deliver) { this.deliver = deliver; this.buffer = Buffer.alloc(0); }
    feed(chunk) {
        requireThat(this.buffer.length + chunk.length <= MAX_BODY + 5, 'mqtt_buffer_limit');
        this.buffer = Buffer.concat([this.buffer, chunk]);
        while (this.buffer.length >= 2) {
            let length = 0;
            let offset = 1;
            let byte;
            do {
                if (offset >= this.buffer.length) return;
                requireThat(offset <= 4, 'mqtt_length_encoding');
                byte = this.buffer[offset];
                length += (byte & 127) * 128 ** (offset - 1);
                offset++;
            } while (byte & 128);
            requireThat(length <= MAX_BODY, 'mqtt_packet_limit');
            if (this.buffer.length < offset + length) return;
            const packet = { header: this.buffer[0], type: this.buffer[0] >> 4,
                body: Buffer.from(this.buffer.subarray(offset, offset + length)) };
            this.buffer = this.buffer.subarray(offset + length);
            if (packet.type === 3) {
                requireThat(packet.header === 0x30 && packet.body.length >= 2, 'mqtt_publish_flags');
                const topicLength = packet.body.readUInt16BE(0);
                requireThat(topicLength > 0 && 2 + topicLength < packet.body.length, 'mqtt_publish_length');
                packet.topic = packet.body.subarray(2, 2 + topicLength).toString();
                try { packet.message = JSON.parse(packet.body.subarray(2 + topicLength).toString()); }
                catch { throw new SmokeFailure('mqtt_json_invalid'); }
                requireThat(packet.message && typeof packet.message === 'object', 'mqtt_json_invalid');
            }
            this.deliver(packet);
        }
    }
}

class Queue {
    constructor() { this.items = []; this.waiter = null; this.error = null; }
    push(value) {
        if (this.error) return;
        if (this.waiter) { const waiter = this.waiter; this.waiter = null; waiter.resolve(value); }
        else { requireThat(this.items.length < 256, 'event_queue_limit'); this.items.push(value); }
    }
    fail(error) {
        if (this.error) return;
        this.error = error instanceof SmokeFailure ? error : new SmokeFailure('bounded_runtime_failure');
        if (this.waiter) { const waiter = this.waiter; this.waiter = null; waiter.reject(this.error); }
    }
    next(deadline) {
        if (this.error) return Promise.reject(this.error);
        if (this.items.length) return Promise.resolve(this.items.shift());
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.waiter = null;
                reject(new SmokeFailure('candidate_turn_timeout'));
            }, Math.max(1, deadline - Date.now()));
            this.waiter = {
                resolve: value => { clearTimeout(timer); resolve(value); },
                reject: error => { clearTimeout(timer); reject(error); }
            };
        });
    }
    check() { if (this.error) throw this.error; }
}

async function loadCodec(modulePath) {
    try {
        const opus = await import(pathToFileURL(modulePath).href);
        const encoder = await opus.createEncoder({ channels: 1, sampleRate: 16000, frameSize: FRAME_SAMPLES,
            application: opus.Application.Audio, dtx: false });
        const decoder = await opus.createDecoder({ channels: 1, sampleRate: 16000, maxFrameSize: FRAME_SAMPLES });
        return { opus, encoder, decoder };
    } catch { throw new SmokeFailure('opus_module_unavailable'); }
}

async function opusFixture(codec) {
    const packets = [];
    for (let index = 0; index < FRAME_COUNT; index++) {
        const pcm = new Int16Array(FRAME_SAMPLES);
        for (let sample = 0; sample < FRAME_SAMPLES; sample++) {
            pcm[sample] = Math.round(6000 * Math.sin(2 * Math.PI * 440 * (index * FRAME_SAMPLES + sample) / 16000));
        }
        const packet = Buffer.from(codec.encoder.encode(pcm, { frameSize: FRAME_SAMPLES }));
        const info = await codec.opus.getPacketInfo(packet, { sampleRate: 16000 });
        requireThat(info.samples === FRAME_SAMPLES && info.channels === 1 && info.durationMs === 60, 'input_opus_format');
        packets.push(packet);
    }
    return packets;
}

function udpPacket(nonce, key, opus, timestamp, sequence) {
    requireThat(opus.length > 0 && opus.length <= 65535, 'udp_payload_limit');
    const header = Buffer.from(nonce);
    header.writeUInt16BE(opus.length, 2);
    header.writeUInt32BE(timestamp, 8);
    header.writeUInt32BE(sequence, 12);
    const cipher = crypto.createCipheriv('aes-128-ctr', key, header);
    return Buffer.concat([header, cipher.update(opus), cipher.final()]);
}

function decryptUdp(packet, rinfo, session, previousSequence) {
    requireThat(rinfo.address === HOST && rinfo.port === UDP_PORT, 'udp_origin_mismatch');
    requireThat(packet.length >= 17 && packet[0] === 1 && packet[1] === 0, 'udp_header_invalid');
    requireThat(packet.length === 16 + packet.readUInt16BE(2), 'udp_length_mismatch');
    requireThat(packet.readUInt32BE(4) === session.nonce.readUInt32BE(4), 'udp_connection_mismatch');
    const sequence = packet.readUInt32BE(12);
    requireThat(sequence === previousSequence + 1, 'udp_packet_loss_or_reorder');
    const decipher = crypto.createDecipheriv('aes-128-ctr', session.key, packet.subarray(0, 16));
    return { sequence, opus: Buffer.concat([decipher.update(packet.subarray(16)), decipher.final()]) };
}

function helloSession(message) {
    requireThat(message.type === 'hello' && message.version === 3 && message.transport === 'udp' &&
        typeof message.session_id === 'string' && message.session_id.length > 0 && message.session_id.length <= 128, 'invalid_hello');
    requireThat(message.audio_params && Object.keys(message.audio_params).length === Object.keys(AUDIO).length &&
        Object.entries(AUDIO).every(([key, value]) => message.audio_params[key] === value), 'hello_audio_format');
    requireThat(message.udp?.server === HOST && message.udp?.port === UDP_PORT &&
        message.udp?.encryption === 'aes-128-ctr', 'udp_destination_rejected');
    requireThat(/^[0-9a-f]{32}$/.test(message.udp.key || '') && /^[0-9a-f]{32}$/.test(message.udp.nonce || ''), 'udp_key_format');
    const nonce = Buffer.from(message.udp.nonce, 'hex');
    requireThat(nonce[0] === 1 && nonce[1] === 0 && nonce.readUInt16BE(2) === 0 &&
        nonce.readUInt32BE(8) === 0 && nonce.readUInt32BE(12) === 0, 'udp_nonce_format');
    return { id: message.session_id, key: Buffer.from(message.udp.key, 'hex'), nonce };
}

function textEvent(state, message, session, counts) {
    requireThat(message.session_id === session.id, 'session_mismatch');
    if (message.type === 'stt') {
        requireThat(state.phase === 'stt' && message.text === ASR_TEXT, 'stt_text_mismatch');
        bump(counts, 'stt'); state.phase = 'start';
    } else if (message.type === 'tts') {
        if (message.state === 'start') {
            requireThat(state.phase === 'start', 'tts_start_order');
            bump(counts, 'tts_start'); state.phase = 'sentence';
        } else if (message.state === 'sentence_start') {
            requireThat(['sentence', 'audio'].includes(state.phase) && typeof message.text === 'string', 'tts_text_order');
            state.text.push(message.text); bump(counts, 'tts_text'); state.phase = 'audio';
        } else if (message.state === 'stop') {
            requireThat(state.phase === 'audio', 'tts_stop_order');
            requireThat(state.text.join('').trim() === SPOKEN_REPLY, 'tts_display_text_mismatch');
            bump(counts, 'tts_stop'); state.phase = 'done';
        } else throw new SmokeFailure('unexpected_tts_state');
    } else if (message.type === 'llm') bump(counts, 'llm_status');
    else throw new SmokeFailure('unexpected_mqtt_event');
}

function outputAudio(packet, rinfo, session, state, codec, counts) {
    const result = decryptUdp(packet, rinfo, session, state.sequence);
    const pcm = codec.decoder.decode(result.opus, { frameSize: FRAME_SAMPLES });
    requireThat(pcm.length === FRAME_SAMPLES, 'invalid_outgoing_opus');
    state.sequence = result.sequence;
    bump(counts, 'outgoing_opus_packets'); bump(counts, 'outgoing_pcm_samples', pcm.length);
    if (pcm.some(sample => sample !== 0)) bump(counts, 'nonzero_audio_packets');
}

async function candidate(codec, packets, counts, timeout, portsOutput) {
    const deadline = Date.now() + timeout * 1000;
    const queue = new Queue();
    const tcp = net.createConnection({ host: HOST, port: MQTT_PORT });
    const udp = dgram.createSocket('udp4');
    let bound = false;
    let active = true;
    let session;
    let keepAlive;
    const output = { sequence: 0 };
    const sendPacket = packet => { requireThat(active && !tcp.destroyed, 'mqtt_connection_closed'); tcp.write(packet); };
    const publish = message => sendPacket(mqttPacket(0x30, Buffer.concat([mqttString(PUBLISH_TOPIC), Buffer.from(JSON.stringify(message))])));
    const parser = new MqttParser(packet => {
        if (packet.type === 13) { bump(counts, 'mqtt_pingresp'); return; }
        if (packet.type === 3) {
            requireThat(packet.topic === REPLY_TOPIC, 'mqtt_reply_topic_mismatch');
            const message = packet.message;
            if (message.type === 'mcp') {
                const payload = message.payload || {};
                if (payload.method === 'notifications/initialized') return;
                requireThat(payload.id !== undefined && ['initialize', 'tools/list'].includes(payload.method), 'unexpected_device_tool_request');
                const result = payload.method === 'initialize' ? {
                    protocolVersion: '2024-11-05', capabilities: { tools: {} },
                    serverInfo: { name: 'synthetic-mqtt-smoke', version: '1' }
                } : { tools: [] };
                publish({ type: 'mcp', payload: { jsonrpc: '2.0', id: payload.id, result } });
                bump(counts, 'device_mcp_replies'); return;
            }
            requireThat(!['error', 'goodbye'].includes(message.type), 'gateway_turn_rejected');
        }
        queue.push(packet);
    });
    tcp.on('data', chunk => { try { parser.feed(chunk); } catch (error) { queue.fail(error); } });
    tcp.on('error', () => queue.fail(new SmokeFailure('mqtt_transport_failed')));
    tcp.on('close', () => { if (active) queue.fail(new SmokeFailure('mqtt_connection_closed')); });
    udp.on('error', () => queue.fail(new SmokeFailure('udp_transport_failed')));
    udp.on('message', (packet, rinfo) => {
        try {
            requireThat(session, 'udp_before_hello');
            outputAudio(packet, rinfo, session, output, codec, counts);
        } catch (error) { queue.fail(error); }
    });
    const next = async predicate => {
        const packet = await queue.next(deadline);
        requireThat(predicate(packet), 'unexpected_mqtt_packet');
        return packet;
    };
    try {
        await new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(new SmokeFailure('mqtt_connect_timeout')), Math.min(5000, deadline - Date.now()));
            tcp.once('connect', () => { clearTimeout(timer); resolve(); });
            tcp.once('error', () => { clearTimeout(timer); reject(new SmokeFailure('mqtt_connect_failed')); });
        });
        await new Promise((resolve, reject) => {
            udp.once('error', () => reject(new SmokeFailure('udp_bind_failed')));
            udp.bind(0, HOST, () => { bound = true; resolve(); });
        });
        if (portsOutput) {
            await writeFile(portsOutput, JSON.stringify({ ip: HOST, port: udp.address().port,
                protocol: 'udp', role: 'mqtt-client' }) + '\n', { mode: 0o644, flag: 'wx' });
        }
        const auth = credentials();
        sendPacket(mqttPacket(0x10, Buffer.concat([mqttString('MQTT'), Buffer.from([4, 0xc2, 0, 60]),
            mqttString(auth.clientId), mqttString(auth.username), mqttString(auth.password)])));
        const connack = await next(packet => packet.type === 2);
        requireThat(connack.header === 0x20 && connack.body.equals(Buffer.from([0, 0])), 'mqtt_connack_rejected');
        bump(counts, 'mqtt_connack');
        keepAlive = setInterval(() => { try { sendPacket(mqttPacket(0xc0)); } catch (error) { queue.fail(error); } }, 10000);
        sendPacket(mqttPacket(0x82, Buffer.concat([Buffer.from([0, 1]), mqttString(REPLY_TOPIC), Buffer.from([0])])));
        const suback = await next(packet => packet.type === 9);
        requireThat(suback.header === 0x90 && suback.body.equals(Buffer.from([0, 1, 0])), 'mqtt_suback_rejected');
        bump(counts, 'mqtt_suback');
        publish({ type: 'hello', version: 3, transport: 'mqtt', audio_params: AUDIO, features: { mcp: false, aec: false, emoji: false } });
        session = helloSession((await next(packet => packet.type === 3 && packet.message.type === 'hello')).message);
        bump(counts, 'hello');
        await delay(1000); queue.check();
        publish({ type: 'listen', state: 'start', mode: 'manual', session_id: session.id });
        bump(counts, 'listen_start');
        // TCP control and UDP audio do not share ordering. A managed-voice pong
        // proves listen-start was processed before the first audio datagram.
        publish({ type: 'ping', session_id: session.id });
        await next(packet => packet.type === 3 && packet.message.type === 'pong');
        bump(counts, 'listen_barrier');
        for (let index = 0; index < packets.length; index++) {
            queue.check(); requireThat(Date.now() < deadline, 'candidate_turn_timeout');
            const packet = udpPacket(session.nonce, session.key, packets[index], index * 60, index + 1);
            await new Promise((resolve, reject) => udp.send(packet, UDP_PORT, HOST, error => error ? reject(new SmokeFailure('udp_send_failed')) : resolve()));
            bump(counts, 'incoming_opus_packets'); bump(counts, 'incoming_pcm_samples', FRAME_SAMPLES);
            await delay(60);
        }
        publish({ type: 'ping', session_id: session.id });
        await next(packet => packet.type === 3 && packet.message.type === 'pong');
        bump(counts, 'audio_barrier');
        await delay(100); queue.check();
        publish({ type: 'listen', state: 'stop', session_id: session.id }); bump(counts, 'listen_stop');
        const state = { phase: 'stt', text: [] };
        while (state.phase !== 'done') {
            const packet = await next(packet => packet.type === 3);
            textEvent(state, packet.message, session, counts);
        }
        // MQTT and UDP are independent transports. Give already-sent tail audio
        // bounded time to arrive after the TCP tts-stop event before final proof.
        requireThat(Date.now() + 500 < deadline, 'candidate_turn_timeout');
        await delay(500); queue.check();
        requireThat(counts.incoming_opus_packets === FRAME_COUNT && counts.incoming_pcm_samples === 19200, 'input_frame_count');
        requireThat(counts.outgoing_opus_packets > 0 && counts.nonzero_audio_packets > 0, 'outgoing_silent_or_missing_audio');
        requireThat(counts.stt === 1 && counts.tts_start === 1 && counts.tts_stop === 1 && counts.tts_text > 0, 'voice_event_count_mismatch');
        bump(counts, 'voice_turn_complete');
        publish({ type: 'goodbye', session_id: session.id });
        sendPacket(mqttPacket(0xe0));
    } finally {
        active = false; clearInterval(keepAlive); tcp.destroy();
        if (bound) await new Promise(resolve => udp.close(resolve)); else { try { udp.close(); } catch {} }
    }
}

async function offline(codec, packets, counts) {
    const auth = credentials();
    requireThat(auth.clientId.split('@@@').length === 3 &&
        auth.password === crypto.createHmac('sha256', SIGNATURE_KEY).update(`${auth.clientId}|${auth.username}`).digest('base64'), 'offline_credentials');
    const hello = { type: 'hello', version: 3, transport: 'udp', session_id: 'offline-synthetic-session', audio_params: AUDIO,
        udp: { server: HOST, port: UDP_PORT, encryption: 'aes-128-ctr', key: '11'.repeat(16), nonce: '01000000123456780000000000000000' } };
    const session = helloSession(hello);
    helloSession({ ...hello, audio_params: { frame_duration: 60, channels: 1, sample_rate: 16000, format: 'opus' } });
    const publish = mqttPacket(0x30, Buffer.concat([mqttString(REPLY_TOPIC), Buffer.from(JSON.stringify(hello))]));
    const bytes = Buffer.concat([mqttPacket(0x20, Buffer.from([0, 0])), mqttPacket(0x90, Buffer.from([0, 1, 0])), publish]);
    const received = [];
    const parser = new MqttParser(packet => received.push(packet));
    for (let index = 0; index < bytes.length; index++) parser.feed(bytes.subarray(index, index + 1));
    requireThat(received.length === 3 && received[0].type === 2 && received[1].type === 9 && received[2].message.session_id === session.id, 'offline_mqtt_fragmentation');
    const together = [];
    new MqttParser(packet => together.push(packet)).feed(bytes);
    requireThat(together.length === 3, 'offline_mqtt_coalescing');
    const state = { sequence: 0 };
    for (let index = 0; index < packets.length; index++) {
        const encrypted = udpPacket(session.nonce, session.key, packets[index], index * 60, index + 1);
        outputAudio(encrypted, { address: HOST, port: UDP_PORT }, session, state, codec, counts);
    }
    requireThat(counts.outgoing_opus_packets === FRAME_COUNT && counts.outgoing_pcm_samples === 19200 &&
        counts.nonzero_audio_packets > 0, 'offline_opus_roundtrip');
    const rejected = action => {
        try { action(); } catch (error) { requireThat(error instanceof SmokeFailure, 'offline_wrong_error'); bump(counts, 'offline_rejections'); return; }
        throw new SmokeFailure('offline_rejection_failed');
    };
    const packet = udpPacket(session.nonce, session.key, packets[0], 0, 1);
    rejected(() => decryptUdp(packet, { address: '192.0.2.1', port: UDP_PORT }, session, 0));
    rejected(() => decryptUdp(packet, { address: HOST, port: 18885 }, session, 0));
    rejected(() => decryptUdp(packet.subarray(1), { address: HOST, port: UDP_PORT }, session, 0));
    rejected(() => decryptUdp(packet, { address: HOST, port: UDP_PORT }, session, 1));
    rejected(() => helloSession({ ...hello, udp: { ...hello.udp, server: 'unapproved.invalid' } }));
    rejected(() => new MqttParser(() => {}).feed(Buffer.from([0x30, 0xff, 0xff, 0xff, 0xff, 0x01])));
    const events = { phase: 'stt', text: [] };
    for (const event of [{ type: 'stt', text: ASR_TEXT }, { type: 'tts', state: 'start' },
        { type: 'tts', state: 'sentence_start', text: SPOKEN_REPLY }, { type: 'tts', state: 'stop' }]) {
        textEvent(events, { ...event, session_id: session.id }, session, counts);
    }
    requireThat(events.phase === 'done', 'offline_voice_events');
    rejected(() => textEvent({ phase: 'stt', text: [] }, { type: 'tts', state: 'start', session_id: session.id }, session, {}));
    rejected(() => textEvent({ phase: 'stt', text: [] }, { type: 'stt', text: ASR_TEXT, session_id: 'different' }, session, {}));
    counts.incoming_opus_packets = packets.length; counts.incoming_pcm_samples = packets.length * FRAME_SAMPLES;
    bump(counts, 'offline_validation_complete');
}

async function main() {
    const counts = {};
    let codec;
    let options;
    try {
        options = argumentsFor(process.argv.slice(2));
        if (options.help) {
            console.log('node service-mqtt-smoke.mjs (--offline|--candidate) --opus-module /absolute/libopus-wasm/dist/index.js [--timeout 10..120]');
            return;
        }
        codec = await loadCodec(options.opusModule);
        const packets = await opusFixture(codec);
        if (options.mode === 'offline') await offline(codec, packets, counts);
        else await candidate(codec, packets, counts, options.timeout, options.portsOutput);
        console.log(JSON.stringify({ result: 'pass', scope: options.mode === 'offline' ? 'offline-mqtt-udp-codec' : 'managed-candidate-mqtt-udp',
            project: PROJECT, fixture: LABEL, counts, matches_ws_expectations: true, egress_proof: false,
            candidate_namespace_verification: 'main-owned', fake_http_counts_observed: false }));
    } catch (error) {
        console.log(JSON.stringify({ result: 'fail', failure: error instanceof SmokeFailure ? error.message : 'bounded_runtime_failure',
            counts, egress_proof: false }));
        process.exitCode = 1;
    } finally { codec?.encoder.free(); codec?.decoder.free(); }
}

await main();
