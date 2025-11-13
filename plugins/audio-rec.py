import asyncio
import os
import time
import wave
import threading
from io import BytesIO
import math
import struct
import tempfile
import platform
import subprocess
import discord

from main import add_help

recording_sessions = {}


def mix_pcm_streams_with_ffmpeg(pcm_paths, output_path):
    ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    inputs = []
    filter_complex = []

    for i, pcm_path in enumerate(pcm_paths):
        inputs += ['-f', 's16le', '-ar', '48000', '-ac', '2', '-i', pcm_path]
        filter_complex.append(f"[{i}:0]")

    filter_complex_str = ''.join(filter_complex) + f"amix=inputs={len(pcm_paths)}:duration=longest[out]"
    cmd = [
        ffmpeg_bin,
        *inputs,
        '-filter_complex', filter_complex_str,
        '-map', '[out]',
        '-ac', '2',  # stereo output
        '-ar', '48000',
        '-y',  # overwrite
        output_path
    ]

    subprocess.run(cmd, check=True)


def save_pcm_to_tempfile(user_id, pcm_data):
    temp_dir = tempfile.gettempdir()
    pcm_path = os.path.join(temp_dir, f"user_{user_id}.pcm")
    with open(pcm_path, 'wb') as f:
        f.write(pcm_data)
    return pcm_path


class AudioSink(discord.sinks.WaveSink):
    def __init__(self, *, filters=None):
        super().__init__(filters=filters)
        self.audio_data = {}
        self.last_write_time = {}
        self.start_time = time.time()
        self.first_packet_time = {}

        self.sample_rate = 48000
        self.channels = 2
        self.bits_per_sample = 16

    def write(self, data, user):
        # Add safety check for empty or malformed data
        if not data or len(data) < 4:
            return

        # Resolve user_id with better error handling
        if isinstance(user, int):  # SSRC passed
            try:
                user_id = self.vc.ws.ssrc_map[user]["user_id"]
            except (KeyError, AttributeError, TypeError):
                user_id = f"ssrc_{user}"
        else:
            user_id = getattr(user, 'id', str(user))

        now = time.time()

        # Ensure audio buffer exists
        if user_id not in self.audio_data:
            self.audio_data[user_id] = BytesIO()
            # Calculate silence padding from recording start to first packet
            silence_from_start = now - self.start_time
            if silence_from_start > 0:
                bytes_per_sample = self.bits_per_sample // 8
                frame_size = bytes_per_sample * self.channels
                silence_frames = int(self.sample_rate * silence_from_start)
                silence_bytes = b'\x00' * silence_frames * frame_size
                self.audio_data[user_id].write(silence_bytes)

            self.first_packet_time[user_id] = now
            self.last_write_time[user_id] = now
        else:
            # Calculate silence padding based on gap since last write
            last_time = self.last_write_time.get(user_id, now)
            time_gap = now - last_time

            if time_gap > 0.05:  # Only pad if gap is significant
                silence_duration = time_gap
                bytes_per_sample = self.bits_per_sample // 8
                frame_size = bytes_per_sample * self.channels
                silence_frames = int(self.sample_rate * silence_duration)
                silence_bytes = b'\x00' * silence_frames * frame_size
                self.audio_data[user_id].write(silence_bytes)

        # Write actual audio data
        try:
            self.audio_data[user_id].write(data)
            self.last_write_time[user_id] = now
        except Exception as e:
            print(f"Error writing audio data for user {user_id}: {e}")

    def synchronize_audio_streams(self):
        """Synchronize all audio streams to start from the same time reference"""
        if not self.audio_data:
            return {}

        # Find the earliest start time (recording start time)
        earliest_time = self.start_time

        synchronized_data = {}
        bytes_per_sample = self.bits_per_sample // 8
        frame_size = bytes_per_sample * self.channels

        for user_id, buffer in self.audio_data.items():
            try:
                audio_data = buffer.getvalue()

                # Calculate how much silence to add at the beginning
                user_start_time = self.first_packet_time.get(user_id, self.start_time)
                silence_duration = user_start_time - earliest_time

                if silence_duration > 0:
                    silence_frames = int(self.sample_rate * silence_duration)
                    silence_padding = b'\x00' * silence_frames * frame_size
                    # Create new buffer with silence padding + actual audio
                    synchronized_buffer = BytesIO()
                    synchronized_buffer.write(silence_padding)
                    synchronized_buffer.write(audio_data)
                    synchronized_data[user_id] = synchronized_buffer
                else:
                    # No padding needed, just copy the buffer
                    synchronized_buffer = BytesIO()
                    synchronized_buffer.write(audio_data)
                    synchronized_data[user_id] = synchronized_buffer
            except Exception as e:
                print(f"Error synchronizing audio for user {user_id}: {e}")
                continue

        return synchronized_data

    def cleanup(self):
        # Override cleanup to handle BytesIO objects properly
        for user_id, audio_buffer in self.audio_data.items():
            if hasattr(audio_buffer, 'close'):
                try:
                    audio_buffer.close()
                except:
                    pass
        self.audio_data.clear()

        # Call parent cleanup if it exists
        try:
            super().cleanup()
        except AttributeError:
            pass


class RecordingSession:
    def __init__(self, channel, user, combine_audio=False):
        self.channel = channel
        self.user = user
        self.combine_audio = combine_audio
        self.sink = AudioSink()
        self.vc = None
        self.start_time = time.time()
        self.is_recording = False

    async def start_recording(self):
        try:
            # Get bot instance from global scope
            existing_vc = discord.utils.get(bot.voice_clients, guild=self.channel.guild)

            if existing_vc:
                self.vc = existing_vc
            else:
                self.vc = await self.channel.connect()

            # Set the vc reference in the sink
            self.sink.vc = self.vc

            self.vc.start_recording(
                self.sink,
                self.recording_finished,
                sync_start=False
            )

            self.is_recording = True
            return True

        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    async def recording_finished(self, sink, *args):
        pass

    async def stop_recording(self):
        if self.vc and self.is_recording:
            try:
                self.vc.stop_recording()
                self.is_recording = False
                await self.process_and_send_audio()
            except Exception as e:
                print(f"Error during recording processing: {e}")
                await self.user.send(f"Error processing recording: {e}")

    async def process_and_send_audio(self):
        if not self.sink.audio_data:
            await self.user.send("No audio was recorded.")
            return

        sample_rate = 48000
        channels = 2
        bits_per_sample = 16
        bytes_per_sample = bits_per_sample // 8
        frame_size = channels * bytes_per_sample
        max_chunk_size = 8 * 1024 * 1024
        max_audio_bytes = max_chunk_size - 44

        # Synchronize all audio streams to the same timeline
        synchronized_data = self.sink.synchronize_audio_streams()

        if self.combine_audio:
            try:
                pcm_paths = []
                for user_id, buffer in synchronized_data.items():
                    pcm_data = buffer.getvalue()
                    if len(pcm_data) > 0:  # Only process non-empty audio
                        pcm_path = save_pcm_to_tempfile(user_id, pcm_data)
                        pcm_paths.append(pcm_path)

                if pcm_paths:
                    output_wav_path = os.path.join(tempfile.gettempdir(),
                                                   f"combined_recording_{int(self.start_time)}.wav")
                    mix_pcm_streams_with_ffmpeg(pcm_paths, output_wav_path)

                    await self.user.send(
                        file=discord.File(output_wav_path, filename=os.path.basename(output_wav_path))
                    )

                    # Clean up temporary files
                    for pcm_path in pcm_paths:
                        try:
                            os.remove(pcm_path)
                        except:
                            pass
                    try:
                        os.remove(output_wav_path)
                    except:
                        pass
                else:
                    await self.user.send("No audio data to combine.")

            except Exception as e:
                print(f"Error combining audio: {e}")
                await self.user.send(f"Error combining audio: {e}")

        else:
            for user_id, audio_buffer in synchronized_data.items():
                audio_data = audio_buffer.getvalue()
                if len(audio_data) == 0:
                    continue

                total_length = len(audio_data)
                num_chunks = math.ceil(total_length / max_audio_bytes)

                for i in range(num_chunks):
                    start = i * max_audio_bytes
                    end = min((i + 1) * max_audio_bytes, total_length)
                    chunk_data = audio_data[start:end]

                    wav_buffer = self.build_wav(chunk_data, sample_rate, channels, bits_per_sample)
                    filename = f"recording_{user_id}_{int(self.start_time)}" + (
                        f"_part_{i + 1}.wav" if num_chunks > 1 else ".wav")
                    try:
                        await self.user.send(
                            f"Recording from user <@{user_id}>" + (
                                f" - part {i + 1}/{num_chunks}" if num_chunks > 1 else "") + ":",
                            file=discord.File(wav_buffer, filename=filename)
                        )
                    except discord.Forbidden:
                        await self.channel.send(f"Couldn't send the audio to <@{self.user.id}>. Please open your DMs!")
                    except Exception as e:
                        print(f"Error sending audio file: {e}")

        # Clean up synchronized data
        for buffer in synchronized_data.values():
            if hasattr(buffer, 'close'):
                try:
                    buffer.close()
                except:
                    pass

        if self.vc and self.vc.is_connected():
            await self.vc.disconnect()
        self.sink.cleanup()

    def build_wav(self, audio_data, sample_rate, channels, bits_per_sample):
        bytes_per_sample = bits_per_sample // 8
        frame_size = channels * bytes_per_sample
        byte_rate = sample_rate * frame_size
        data_size = len(audio_data)
        wav_size = 36 + data_size

        wav_buffer = BytesIO()
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', wav_size))
        wav_buffer.write(b'WAVE')
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<IHHIIHH',
                                     16,  # Subchunk1Size
                                     1,  # PCM
                                     channels,
                                     sample_rate,
                                     byte_rate,
                                     frame_size,
                                     bits_per_sample
                                     ))
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', data_size))
        wav_buffer.write(audio_data)
        wav_buffer.seek(0)
        return wav_buffer


# You'll need to define bot somewhere in your main.py or import it
# from main import bot

@bot.group(name='rec', invoke_without_command=True)
async def record(ctx):
    """Recording commands"""
    await ctx.send(
        f"Use `{bot.command_prefix}rec start` to start recording or `{bot.command_prefix}rec stop` to stop recording.")


add_help('Utils', 'rec', 'Voice Recording')


@record.command(name='start')
async def start_recording(ctx, combine: str = 'false'):
    """Start recording the voice channel"""

    # Check if user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to start recording!")
        return

    if ctx.guild.id in recording_sessions:
        await ctx.send("Already recording in this server!")
        return

    channel = ctx.author.voice.channel

    # Create recording session
    session = RecordingSession(channel, ctx.author, combine_audio=combine.lower() == 'true')
    recording_sessions[ctx.guild.id] = session

    # Start recording
    success = await session.start_recording()

    if success:
        await ctx.send(f"Started recording in {channel.name}! Use `.rec stop` to stop recording.")
    else:
        if ctx.guild.id in recording_sessions:
            del recording_sessions[ctx.guild.id]
        await ctx.send("Failed to start recording. Make sure I have permission to join voice channels.")


@record.command(name='stop')
async def stop_recording(ctx):
    """Stop recording the voice channel"""

    # Check if recording in this guild
    if ctx.guild.id not in recording_sessions:
        await ctx.send("Not currently recording in this server!")
        return

    session = recording_sessions[ctx.guild.id]

    # Check if the user who started recording is stopping it
    if session.user.id != ctx.author.id:
        await ctx.send("Only the user who started the recording can stop it!")
        return

    await ctx.send("Stopping recording and processing audio...")

    try:
        # Stop recording (this will process and send audio)
        await session.stop_recording()

        # Clean up after processing is complete
        if ctx.guild.id in recording_sessions:
            del recording_sessions[ctx.guild.id]
        await ctx.send("Recording stopped! Check your DMs for the audio file(s).")

    except Exception as e:
        print(f"Error in stop_recording command: {e}")
        await ctx.send(f"Error stopping recording: {e}")

        # Clean up even if there was an error
        if ctx.guild.id in recording_sessions:
            del recording_sessions[ctx.guild.id]


# You'll need to define this decorator or import it from your main file
@when_voice_state_update
async def rec_cleanup_engine(member, before, after):
    if member == bot.user and before.channel and not after.channel:
        guild_id = before.channel.guild.id
        if guild_id in recording_sessions:
            del recording_sessions[guild_id]