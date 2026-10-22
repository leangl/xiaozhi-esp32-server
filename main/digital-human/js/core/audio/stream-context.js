import BlockingQueue from '../../utils/blocking-queue.js?v=0205';
import { log } from '../../utils/logger.js?v=0205';

// Streaming audio playback context
export class StreamingContext {
    constructor(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
        this.opusDecoder = opusDecoder;
        this.audioContext = audioContext;

        // Audio parameters
        this.sampleRate = sampleRate;
        this.channels = channels;
        this.minAudioDuration = minAudioDuration;

        // Initialize queues and state
        this.queue = [];          // Decoded PCM queue: playing
        this.activeQueue = new BlockingQueue(); // Decoded PCM queue: ready to play
        this.pendingAudioBufferQueue = [];  // Pending buffer queue
        this.audioBufferQueue = new BlockingQueue();  // Buffer queue
        this.playing = false;     // Whether playback is active
        this.endOfStream = false; // Whether end-of-stream was received
        this.source = null;       // Current audio source
        this.totalSamples = 0;    // Cumulative sample count
        this.lastPlayTime = 0;    // Last playback timestamp
        this.scheduledEndTime = 0; // End time of scheduled audio

        // Initialize the analyser node for Live2D
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
    }

    // Buffer audio arrays
    pushAudioBuffer(item) {
        this.audioBufferQueue.enqueue(...item);
    }

    // Read buffers to process; single-threaded updates to audioBufferQueue are safe
    async getPendingAudioBufferQueue() {
        // Wait for and retrieve data
        const data = await this.audioBufferQueue.dequeue();
        // Assign the pending queue
        this.pendingAudioBufferQueue = data;
    }

    // Read decoded PCM for playback; single-threaded updates to activeQueue are safe
    async getQueue(minSamples) {
        const num = minSamples - this.queue.length > 0 ? minSamples - this.queue.length : 1;

        // Wait for and retrieve data
        const tempArray = await this.activeQueue.dequeue(num);
        this.queue.push(...tempArray);
    }

    // Convert Int16 audio to Float32
    convertInt16ToFloat32(int16Data) {
        const float32Data = new Float32Array(int16Data.length);
        for (let i = 0; i < int16Data.length; i++) {
            // Map [-32768,32767] to [-1,1], dividing by 32768.0 consistently to avoid asymmetric distortion
            float32Data[i] = int16Data[i] / 32768.0;
        }
        return float32Data;
    }

    // Get the number of packets awaiting decoding
    getPendingDecodeCount() {
        return this.audioBufferQueue.length + this.pendingAudioBufferQueue.length;
    }

    // Get pending playback samples as packets of 960 samples
    getPendingPlayCount() {
        // Count samples already queued
        const queuedSamples = this.activeQueue.length + this.queue.length;

        // Count scheduled but not yet played samples in Web Audio buffers
        let scheduledSamples = 0;
        if (this.playing && this.scheduledEndTime) {
            const currentTime = this.audioContext.currentTime;
            const remainingTime = Math.max(0, this.scheduledEndTime - currentTime);
            scheduledSamples = Math.floor(remainingTime * this.sampleRate);
        }

        const totalSamples = queuedSamples + scheduledSamples;
        return Math.ceil(totalSamples / 960);
    }

    // Clear all audio buffers
    clearAllBuffers() {
        log('Clear all audio buffers', 'info');

        // Clear all queues (use clear to retain object references)
        this.audioBufferQueue.clear();
        this.pendingAudioBufferQueue = [];
        this.activeQueue.clear();
        this.queue = [];

        // Stop the current audio source
        if (this.source) {
            try {
                this.source.stop();
                this.source.disconnect();
            } catch (e) {
                // Ignore errors from already stopped sources
            }
            this.source = null;
        }

        // Reset state
        this.playing = false;
        this.scheduledEndTime = this.audioContext.currentTime;
        this.totalSamples = 0;

        log('Audio buffers cleared', 'success');
    }

    // Get the analyser node for Live2D
    getAnalyser() {
        return this.analyser;
    }

    // Decode Opus to PCM
    async decodeOpusFrames() {
        if (!this.opusDecoder) {
            log('Cannot decode: Opus decoder is not initialized', 'error');
            return;
        } else {
            log('Opus decoder started', 'info');
        }

        while (true) {
            let decodedSamples = [];
            for (const frame of this.pendingAudioBufferQueue) {
                try {
                    // Decode using the Opus decoder
                    const frameData = this.opusDecoder.decode(frame);
                    if (frameData && frameData.length > 0) {
                        // Convert to Float32
                        const floatData = this.convertInt16ToFloat32(frameData);
                        // Use a loop instead of the spread operator
                        for (let i = 0; i < floatData.length; i++) {
                            decodedSamples.push(floatData[i]);
                        }
                    }
                } catch (error) {
                    log("Opus decoding failed: " + error.message, 'error');
                }
            }

            if (decodedSamples.length > 0) {
                // Use a loop instead of the spread operator
                for (let i = 0; i < decodedSamples.length; i++) {
                    this.activeQueue.enqueue(decodedSamples[i]);
                }
                this.totalSamples += decodedSamples.length;
            } else {
                log('No samples were successfully decoded', 'warning');
            }
            await this.getPendingAudioBufferQueue();
        }
    }

    // Start audio playback
    async startPlaying() {
        this.scheduledEndTime = this.audioContext.currentTime; // Track the end time of scheduled audio

        while (true) {
            // Initial buffering: wait for enough samples before playback
            const minSamples = this.sampleRate * this.minAudioDuration * 2;
            if (!this.playing && this.queue.length < minSamples) {
                await this.getQueue(minSamples);
            }
            this.playing = true;

            // Continuously play queued audio in small chunks
            while (this.playing && this.queue.length > 0) {
                // Play 120 ms of audio at a time (two Opus packets)
                const playDuration = 0.12;
                const targetSamples = Math.floor(this.sampleRate * playDuration);
                const actualSamples = Math.min(this.queue.length, targetSamples);

                if (actualSamples === 0) break;

                const currentSamples = this.queue.splice(0, actualSamples);
                const audioBuffer = this.audioContext.createBuffer(this.channels, currentSamples.length, this.sampleRate);
                audioBuffer.copyToChannel(new Float32Array(currentSamples), 0);

                // Create the audio source
                this.source = this.audioContext.createBufferSource();
                this.source.buffer = audioBuffer;

                // Schedule playback precisely
                const currentTime = this.audioContext.currentTime;
                const startTime = Math.max(this.scheduledEndTime, currentTime);

                // Connect to the analyser and output
                this.source.connect(this.analyser);
                this.source.connect(this.audioContext.destination);

                log(`Scheduled ${currentSamples.length} samples, about ${(currentSamples.length / this.sampleRate).toFixed(2)} seconds`, 'debug');
                this.source.start(startTime);

                // Update the next audio chunk's scheduled time
                const duration = audioBuffer.duration;
                this.scheduledEndTime = startTime + duration;
                this.lastPlayTime = startTime;

                // Wait for new data if the queue is insufficient
                if (this.queue.length < targetSamples) {
                    break;
                }
            }

            // Wait for new data
            await this.getQueue(minSamples);
        }
    }
}

// Factory for streamingContext instances
export function createStreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
    return new StreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration);
}
