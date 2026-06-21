import os
import time
import struct
import tempfile
import platform
import subprocess
import math
import threading
from io import BytesIO

import discord

from main import loge, logw, bot, has_required_perm, add_help, when_voice_state_update

# NOTE: bot, add_help, has_required_perm, when_voice_state_update, logw, loge, log
# are all injected into this module's globals by main.py's plugin loader (exec()).
# They are not imported here so this file still works standalone in an IDE.

recording_sessions = {}

REC_SAMPLE_RATE = 48000
REC_CHANNELS = 2
REC_BITS_PER_SAMPLE = 16
REC_BYTES_PER_SAMPLE = REC_BITS_PER_SAMPLE // 8
REC_FRAME_SIZE = REC_CHANNELS * REC_BYTES_PER_SAMPLE


def get_ffmpeg_bin():
    """Resolve ffmpeg the same way main.py does (downloaded next to the script),
    falling back to PATH if that file isn't there for some reason."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(os.path.dirname(script_dir), "ffmpeg")
    if platform.system() == "Windows":
        candidate += ".exe"
    if os.path.exists(candidate):
        return candidate
    return "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"


def mix_pcm_streams_with_ffmpeg(pcm_paths, output_path):
    ffmpeg_bin = get_ffmpeg_bin()
    inputs = []
    filter_inputs = []

    for i, pcm_path in enumerate(pcm_paths):
        inputs += ["-f", "s16le", "-ar", str(REC_SAMPLE_RATE), "-ac", str(REC_CHANNELS), "-i", pcm_path]
        filter_inputs.append(f"[{i}:0]")

    filter_complex = "".join(filter_inputs) + f"amix=inputs={len(pcm_paths)}:duration=longest[out]"
    cmd = [
        ffmpeg_bin,
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ac", str(REC_CHANNELS),
        "-ar", str(REC_SAMPLE_RATE),
        "-y",
        output_path,
    ]

    subprocess.run(cmd, check=True, capture_output=True)


def save_pcm_to_tempfile(user_id, pcm_data):
    temp_dir = tempfile.gettempdir()
    pcm_path = os.path.join(temp_dir, f"rec_user_{user_id}_{int(time.time() * 1000)}.pcm")
    with open(pcm_path, "wb") as f:
        f.write(pcm_data)
    return pcm_path


def build_wav(audio_data, sample_rate=REC_SAMPLE_RATE, channels=REC_CHANNELS, bits_per_sample=REC_BITS_PER_SAMPLE):
    bytes_per_sample = bits_per_sample // 8
    frame_size = channels * bytes_per_sample
    byte_rate = sample_rate * frame_size
    data_size = len(audio_data)
    wav_size = 36 + data_size

    wav_buffer = BytesIO()
    wav_buffer.write(b"RIFF")
    wav_buffer.write(struct.pack("<I", wav_size))
    wav_buffer.write(b"WAVE")
    wav_buffer.write(b"fmt ")
    wav_buffer.write(struct.pack(
        "<IHHIIHH",
        16,             # Subchunk1Size
        1,              # PCM
        channels,
        sample_rate,
        byte_rate,
        frame_size,
        bits_per_sample,
    ))
    wav_buffer.write(b"data")
    wav_buffer.write(struct.pack("<I", data_size))
    wav_buffer.write(audio_data)
    wav_buffer.seek(0)
    return wav_buffer


class AudioSink(discord.sinks.core.Sink):
    """
    Custom raw-PCM sink. We do NOT subclass WaveSink because WaveSink expects its
    own internal AudioData wrapper for cleanup()/format_audio() -- mixing that with
    manually-managed BytesIO buffers caused the previous version's cleanup crashes.
    Instead we own the entire buffer lifecycle ourselves and never call super().cleanup().

    py-cord 2.8.0 contract (confirmed against the installed library):
      write(self, data: discord.voice.VoiceData, user: discord.Member | discord.User | discord.Object)
    `data.pcm` is already-decoded PCM bytes; `user` is already resolved (not an SSRC int).
    """

    def __init__(self, *, filters=None):
        super().__init__(filters=filters)
        self.audio_buffers = {}       # user_id (int) -> BytesIO
        self.last_write_time = {}     # user_id -> float (time.time())
        self.first_packet_time = {}   # user_id -> float (time.time())
        self.start_time = time.time()
        self.lock = threading.Lock()

    def _resolve_user_id(self, user):
        # user is a Member/User/Object on 2.8.0 - just take .id with a safe fallback.
        user_id = getattr(user, "id", None)
        if user_id is None:
            user_id = str(user)
        return user_id

    def write(self, data, user):
        pcm = getattr(data, "pcm", None)
        if not pcm:
            return

        user_id = self._resolve_user_id(user)
        now = time.time()

        with self.lock:
            if user_id not in self.audio_buffers:
                self.audio_buffers[user_id] = BytesIO()

                # Pad with silence from recording start to this user's first packet,
                # so every user's track starts aligned to the same timeline.
                silence_duration = now - self.start_time
                if silence_duration > 0:
                    silence_frames = int(REC_SAMPLE_RATE * silence_duration)
                    self.audio_buffers[user_id].write(b"\x00" * silence_frames * REC_FRAME_SIZE)

                self.first_packet_time[user_id] = now
            else:
                # Pad gaps between packets (pauses in speech) so playback timing stays correct.
                last_time = self.last_write_time.get(user_id, now)
                gap = now - last_time
                if gap > 0.05:
                    silence_frames = int(REC_SAMPLE_RATE * gap)
                    self.audio_buffers[user_id].write(b"\x00" * silence_frames * REC_FRAME_SIZE)

            self.audio_buffers[user_id].write(pcm)
            self.last_write_time[user_id] = now

    def get_synchronized_buffers(self):
        """Returns {user_id: BytesIO} with each buffer already aligned to start_time."""
        with self.lock:
            return {user_id: buf for user_id, buf in self.audio_buffers.items() if buf.getbuffer().nbytes > 0}

    def cleanup(self):
        # Deliberately does NOT call super().cleanup() - the base implementation expects
        # AudioData objects with their own .cleanup()/format_audio() hooks that we don't use.
        with self.lock:
            for buf in self.audio_buffers.values():
                try:
                    buf.close()
                except Exception:
                    pass
            self.audio_buffers.clear()


class RecordingSession:
    def __init__(self, channel, user, combine_audio=False):
        self.channel = channel
        self.user = user
        self.combine_audio = combine_audio
        self.sink = AudioSink()
        self.vc = None
        self.start_time = time.time()
        self.is_recording = False
        self._loop = None

    async def start_recording(self):
        try:
            existing_vc = discord.utils.get(bot.voice_clients, guild=self.channel.guild)
            self.vc = existing_vc if existing_vc else await self.channel.connect()

            import asyncio
            self._loop = asyncio.get_event_loop()

            # py-cord 2.8.0: callback signature is now after(exception), called from
            # a non-async context internally but still needs to be a coroutine function
            # per start_recording's typing; args/sync_start are deprecated and ignored.
            self.vc.start_recording(self.sink, self.recording_finished)

            self.is_recording = True
            return True
        except Exception as e:
            logw(f"[VoiceRecording] Error starting recording: {e}")
            return False

    async def recording_finished(self, exception=None):
        if exception:
            loge(f"[VoiceRecording] Recording stopped with error: {exception}")

    async def stop_recording(self):
        if not (self.vc and self.is_recording):
            return
        try:
            self.vc.stop_recording()
            self.is_recording = False
            # Give the background packet router a brief moment to flush remaining packets.
            import asyncio
            await asyncio.sleep(0.5)
            await self.process_and_send_audio()
        except Exception as e:
            loge(f"[VoiceRecording] Error during recording processing: {e}")
            try:
                await self.user.send(f"Error processing recording: {e}")
            except discord.Forbidden:
                pass

    async def process_and_send_audio(self):
        buffers = self.sink.get_synchronized_buffers()

        if not buffers:
            try:
                await self.user.send("No audio was recorded.")
            except discord.Forbidden:
                pass
            await self._disconnect_and_cleanup()
            return

        max_chunk_size = 8 * 1024 * 1024
        max_audio_bytes = max_chunk_size - 44  # leave room for the WAV header

        if self.combine_audio:
            await self._send_combined(buffers)
        else:
            await self._send_per_user(buffers, max_audio_bytes)

        await self._disconnect_and_cleanup()

    async def _send_combined(self, buffers):
        pcm_paths = []
        output_wav_path = None
        try:
            for user_id, buf in buffers.items():
                pcm_data = buf.getvalue()
                if pcm_data:
                    pcm_paths.append(save_pcm_to_tempfile(user_id, pcm_data))

            if not pcm_paths:
                await self.user.send("No audio data to combine.")
                return

            output_wav_path = os.path.join(
                tempfile.gettempdir(), f"combined_recording_{int(self.start_time)}.wav"
            )
            mix_pcm_streams_with_ffmpeg(pcm_paths, output_wav_path)

            await self.user.send(
                "Here is the combined recording from the voice channel:",
                file=discord.File(output_wav_path, filename=os.path.basename(output_wav_path)),
            )
        except subprocess.CalledProcessError as e:
            loge(f"[VoiceRecording] ffmpeg failed: {e}")
            await self.user.send("Failed to combine audio (ffmpeg error). Check bot logs.")
        except discord.Forbidden:
            await self.channel.send(f"Couldn't DM the recording to <@{self.user.id}>. Please open your DMs!")
        except Exception as e:
            loge(f"[VoiceRecording] Error combining audio: {e}")
            try:
                await self.user.send(f"Error combining audio: {e}")
            except discord.Forbidden:
                pass
        finally:
            for path in pcm_paths:
                try:
                    os.remove(path)
                except OSError:
                    pass
            if output_wav_path:
                try:
                    os.remove(output_wav_path)
                except OSError:
                    pass

    async def _send_per_user(self, buffers, max_audio_bytes):
        for user_id, buf in buffers.items():
            audio_data = buf.getvalue()
            if not audio_data:
                continue

            total_length = len(audio_data)
            num_chunks = math.ceil(total_length / max_audio_bytes)

            for i in range(num_chunks):
                start = i * max_audio_bytes
                end = min((i + 1) * max_audio_bytes, total_length)
                chunk_data = audio_data[start:end]

                wav_buffer = build_wav(chunk_data)
                filename = (
                    f"recording_{user_id}_{int(self.start_time)}"
                    + (f"_part_{i + 1}.wav" if num_chunks > 1 else ".wav")
                )
                try:
                    await self.user.send(
                        f"Recording from user <@{user_id}>"
                        + (f" - part {i + 1}/{num_chunks}" if num_chunks > 1 else "")
                        + ":",
                        file=discord.File(wav_buffer, filename=filename),
                    )
                except discord.Forbidden:
                    await self.channel.send(
                        f"Couldn't DM the recording to <@{self.user.id}>. Please open your DMs!"
                    )
                    return
                except Exception as e:
                    loge(f"[VoiceRecording] Error sending audio file: {e}")

    async def _disconnect_and_cleanup(self):
        if self.vc and self.vc.is_connected():
            try:
                await self.vc.disconnect()
            except Exception as e:
                logw(f"[VoiceRecording] Error disconnecting: {e}")
        self.sink.cleanup()


@bot.group(name="rec", invoke_without_command=True)
async def record(ctx):
    """Recording commands"""
    await ctx.send(
        f"Use `{bot.command_prefix}rec start` to start recording or `{bot.command_prefix}rec stop` to stop recording."
    )


add_help("Utils", "rec", "Voice Recording")


@record.command(name="start")
@has_required_perm()
async def start_recording_cmd(ctx, combine: str = "false"):
    """Start recording the voice channel"""

    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to start recording!")
        return

    if ctx.guild.id in recording_sessions:
        await ctx.send("Already recording in this server!")
        return

    channel = ctx.author.voice.channel

    await ctx.send(
        "⚠️ Starting a recording. Please make sure everyone in the channel is aware "
        "this call is being recorded."
    )

    session = RecordingSession(channel, ctx.author, combine_audio=combine.lower() == "true")
    recording_sessions[ctx.guild.id] = session

    success = await session.start_recording()

    if success:
        await ctx.send(f"Started recording in {channel.name}! Use `{bot.command_prefix}rec stop` to stop recording.")
    else:
        recording_sessions.pop(ctx.guild.id, None)
        await ctx.send(
            "Failed to start recording. Make sure I have permission to join voice channels, "
            "and note that voice recording can currently be unreliable due to Discord's DAVE "
            "end-to-end voice encryption (a known py-cord limitation)."
        )


add_help("Utils", "rec start [combine]", "starts recording the vc you are in, combine true/false to merge into one file")


@record.command(name="stop")
async def stop_recording_cmd(ctx):
    """Stop recording the voice channel"""

    if ctx.guild.id not in recording_sessions:
        await ctx.send("Not currently recording in this server!")
        return

    session = recording_sessions[ctx.guild.id]

    if session.user.id != ctx.author.id:
        await ctx.send("Only the user who started the recording can stop it!")
        return

    await ctx.send("Stopping recording and processing audio...")

    try:
        await session.stop_recording()
        recording_sessions.pop(ctx.guild.id, None)
        await ctx.send("Recording stopped! Check your DMs for the audio file(s).")
    except Exception as e:
        loge(f"[VoiceRecording] Error in stop command: {e}")
        await ctx.send(f"Error stopping recording: {e}")
        recording_sessions.pop(ctx.guild.id, None)


add_help("Utils", "rec stop", "stops the current recording and DMs you the audio")


@when_voice_state_update
async def rec_cleanup_engine(member, before, after):
    if member.id == bot.user.id and before.channel and not after.channel:
        guild_id = before.channel.guild.id
        session = recording_sessions.pop(guild_id, None)
        if session and session.is_recording:
            session.sink.cleanup()