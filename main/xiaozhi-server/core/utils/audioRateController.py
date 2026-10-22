import time
import asyncio
from collections import deque
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class AudioRateController:
    """
    Audio rate controller: precisely pace transmission using 60 ms frames.
    Prevent accumulated timing drift under high concurrency.
    """

    def __init__(self, frame_duration=60, send_delay=0):
        """
        Args:
            frame_duration: Duration of one audio frame in milliseconds; default: 60 ms.
            send_delay: Custom send interval in milliseconds.
                        0 = pace by frame_duration;
                        >0 = pace by send_delay (no main-thread enqueue delay or prebuffering).
        """
        # Pacing interval (ms): use send_delay if positive, otherwise frame_duration.
        self.interval_ms = send_delay if send_delay > 0 else frame_duration
        self.queue = deque()
        self.play_position = 0  # Virtual playback position in milliseconds.
        self.start_timestamp = None  # Start timestamp (read-only during continuous playback).
        self.pending_send_task = None
        self.logger = logger
        self.queue_empty_event = asyncio.Event()  # Queue-empty event.
        self.queue_empty_event.set()  # Initially empty.
        self.queue_has_data_event = asyncio.Event()  # Queue-data event.
        self._last_queue_empty_time = 0  # Last time the queue became empty, in seconds.

    def reset(self):
        """Reset the controller state."""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            # Cancellation is handled on the next event-loop iteration; do not block waiting.

        self.queue.clear()
        self.play_position = 0
        self.start_timestamp = None  # Set by the first audio packet.
        self._last_queue_empty_time = 0  # Reset the timestamp.
        # Update the associated events.
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()

    def add_audio(self, opus_packet):
        """Add an audio packet to the queue."""
        # After an empty queue, adjust the timestamp to maintain playback continuity.
        # This prevents newly queued audio from playing early after a tool-call wait.
        # A gap shorter than one frame is normal streaming and needs no reset.
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            # Treat a gap of at least one frame as resuming after a pause.
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed from empty; timestamp reset, playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("audio", opus_packet))
        # Update the associated events.
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def add_message(self, message_callback):
        """
        Add a message to the queue (send immediately without consuming playback time).

        Args:
            message_callback: Message-sending callback, async def().
        """
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed from empty; timestamp reset, playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("message", message_callback))
        # Update the associated events.
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def _get_elapsed_ms(self):
        """Return elapsed time in milliseconds."""
        if self.start_timestamp is None:
            return 0
        return (time.monotonic() - self.start_timestamp) * 1000

    async def check_queue(self, send_audio_callback):
        """
        Drain queued audio/messages according to the transmission schedule.

        Args:
            send_audio_callback: Audio-sending callback, async def(opus_packet).
        """
        while self.queue:
            item = self.queue[0]
            item_type = item[0]

            if item_type == "message":
                # Messages are sent immediately and do not consume playback time.
                _, message_callback = item
                self.queue.popleft()
                try:
                    await message_callback()
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send message: {e}")
                    raise

            elif item_type == "audio":
                if self.start_timestamp is None:
                    self.start_timestamp = time.monotonic()

                _, opus_packet = item

                # Wait until the scheduled transmission time.
                while True:
                    # Calculate the time difference.
                    elapsed_ms = self._get_elapsed_ms()
                    output_ms = self.play_position

                    if elapsed_ms < output_ms:
                        # Not yet time to send; calculate the remaining wait.
                        wait_ms = output_ms - elapsed_ms

                        # Wait interruptibly, then check again.
                        try:
                            await asyncio.sleep(wait_ms / 1000)
                        except asyncio.CancelledError:
                            self.logger.bind(tag=TAG).debug("Audio transmission task cancelled")
                            raise
                        # Recheck the time by returning to while True.
                    else:
                        # Transmission is due; leave the wait loop.
                        break

                # Transmission is due; remove the packet from the queue and send it.
                self.queue.popleft()
                self.play_position += self.interval_ms
                try:
                    await send_audio_callback(opus_packet)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send audio: {e}")
                    raise

        # Update events after draining the queue.
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()
        self._last_queue_empty_time = time.monotonic()  # Record when the queue became empty.

    def start_sending(self, send_audio_callback):
        """
        Start an asynchronous transmission task.

        Args:
            send_audio_callback: Audio-sending callback.

        Returns:
            asyncio.Task: Transmission task.
        """

        async def _send_loop():
            try:
                while True:
                    # Wait for queued data without CPU-consuming polling.
                    await self.queue_has_data_event.wait()

                    await self.check_queue(send_audio_callback)
            except asyncio.CancelledError:
                self.logger.bind(tag=TAG).debug("Audio transmission loop stopped")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Audio transmission loop error: {e}")

        self.pending_send_task = asyncio.create_task(_send_loop())
        return self.pending_send_task

    def stop_sending(self):
        """Stop the transmission task."""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            self.logger.bind(tag=TAG).debug("Audio transmission task cancelled")
