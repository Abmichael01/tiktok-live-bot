"""
TikTok Live Bot — Voice Agent
==============================
Uses edge-tts (Microsoft Neural TTS, free, no API key) to speak
bot replies out loud on the streamer's PC — viewers hear it through
the stream audio.

Flow:
  trigger fires → text reply → edge-tts generates MP3 → pygame plays it
  (all async, non-blocking — bot keeps reading chat while audio plays)

Requirements:
    pip install edge-tts pygame

Voice options (good English voices):
    en-US-GuyNeural        — Male, confident, American
    en-US-JennyNeural      — Female, friendly, American
    en-GB-RyanNeural       — Male, British
    en-AU-NatashaNeural    — Female, Australian

Change VOICE below or pass voice= when creating VoiceAgent.
"""

import asyncio
import io
import logging
import os
import tempfile
import base64
from pathlib import Path
from typing import Optional, Callable

# -- Try importing pydub for audio conversion ---------------------------------
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not installed — Simli avatar voice will not work")
    logger.warning("Run: pip install pydub")

import edge_tts

logger = logging.getLogger("VoiceAgent")

# ── Default voice — change to taste ──────────────────────────────────────────
DEFAULT_VOICE = "en-US-GuyNeural"
DEFAULT_RATE  = "+0%"     # speed: +10% faster, -10% slower
DEFAULT_VOLUME = "+0%"    # volume: +10% louder, -10% quieter
DEFAULT_PITCH  = "+0Hz"   # pitch: +5Hz higher, -5Hz lower

# ── Try importing pygame for audio playback ───────────────────────────────────
try:
    import pygame
    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not installed — voice will generate but not play")
    logger.warning("Run: pip install pygame")


class VoiceAgent:
    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        volume: str = DEFAULT_VOLUME,
        pitch: str = DEFAULT_PITCH,
        enabled: bool = True,
        on_speak_start=None,
        on_speak_stop=None,
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.enabled = enabled and PYGAME_AVAILABLE
        self.on_speak_start = on_speak_start
        self.on_speak_stop = on_speak_stop

        # Queue so voice replies play sequentially, never overlap
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._speaking = False

        if self.enabled:
            logger.info(f"🔊 Voice agent ready — voice: {voice}")
        else:
            logger.info("🔇 Voice agent disabled (pygame not available or disabled in config)")

    def start(self):
        """Start the background audio worker."""
        if self.enabled:
            self._worker_task = asyncio.create_task(self._audio_worker())
            logger.info("🎙️  Voice worker started")

    def stop(self):
        """Stop the voice agent."""
        if self._worker_task:
            self._worker_task.cancel()
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    async def speak(self, text: str, gesture: Optional[str] = None, metadata: Optional[dict] = None):
        """Queue text to be spoken. Non-blocking."""
        if not self.enabled:
            return
        # Trim text — don't speak emojis or URLs, keep it clean
        clean = self._clean_text(text)
        if clean:
            await self._queue.put({"text": clean, "gesture": gesture, "metadata": metadata})
            logger.info(f"🎙️  Queued speech: {clean[:60]}... (Gesture: {gesture})")

    def _clean_text(self, text: str) -> str:
        """Strip emojis, URLs, and extra whitespace for cleaner TTS output."""
        import re
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        # Remove common emojis (basic range)
        text = re.sub(
            r'[\U00010000-\U0010ffff'
            r'\U0001F600-\U0001F64F'
            r'\U0001F300-\U0001F5FF'
            r'\U0001F680-\U0001F6FF'
            r'\U0001F1E0-\U0001F1FF'
            r'\u2600-\u26FF\u2700-\u27BF]',
            '', text, flags=re.UNICODE
        )
        # Collapse whitespace
        text = ' '.join(text.split())
        return text.strip()

    async def _audio_worker(self):
        """Background worker — generates and plays audio sequentially."""
        while True:
            try:
                item = await self._queue.get()
                text = item["text"]
                gesture = item.get("gesture")
                try:
                    # Re-enabling PCM generation for perfect Simli lip-sync
                    audio_pcm_base64, duration = await self._generate_audio_pcm(text)
                    if audio_pcm_base64:
                        logger.info(f"✅ PCM generated ({len(audio_pcm_base64)} chars, {duration:.2f}s)")
                    else:
                        logger.warning("❌ PCM generation failed")
                    
                    # Notify start with both text and audio data
                    if self.on_speak_start:
                        metadata = item.get("metadata")
                        if asyncio.iscoroutinefunction(self.on_speak_start):
                            await self.on_speak_start(text, gesture, audio=audio_pcm_base64, metadata=metadata)
                        else:
                            self.on_speak_start(text, gesture, audio=audio_pcm_base64, metadata=metadata)

                    # Only play locally if we did NOT generate PCM audio for an avatar.
                    # Otherwise, Simli plays it automatically in the browser!
                    if not audio_pcm_base64:
                        await self._play_audio_locally(text)
                    else:
                        # Sleep for the duration of the audio so the UI status persists
                        await asyncio.sleep(duration)
                except Exception as e:
                    logger.error(f"Voice error: {e}")
                finally:
                    self._speaking = False
                    if self.on_speak_stop:
                        if asyncio.iscoroutinefunction(self.on_speak_stop):
                            await self.on_speak_stop()
                        else:
                            self.on_speak_stop()
                    self._queue.task_done()

                # Small gap between replies
                await asyncio.sleep(0.3)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Audio worker error: {e}")
                await asyncio.sleep(1)

    async def _generate_audio_pcm(self, text: str) -> tuple[Optional[str], float]:
        """Generate (base64_pcm, duration) for Simli."""
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume, pitch=self.pitch)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        
        if not audio_bytes: return None

        # Convert MP3 to PCM16 16kHz using pydub
        try:
            if not PYDUB_AVAILABLE:
                raise ImportError("pydub is not installed. Run 'pip install pydub'")
            
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Get raw pcm bytes
            pcm_bytes = audio_segment.raw_data
            duration = len(pcm_bytes) / 32000.0 # 16000Hz * 1ch * 2 bytes
            return base64.b64encode(pcm_bytes).decode('utf-8'), duration
        except Exception as e:
            if "ffprobe" in str(e).lower() or "ffmpeg" in str(e).lower():
                logger.error("❌ Audio conversion failed: ffmpeg/ffprobe not found on system.")
                logger.error("💡 Fix: Install ffmpeg (https://ffmpeg.org) and add its 'bin' folder to your system PATH.")
            else:
                logger.error(f"Failed to convert audio for Simli: {e}")
            return None, 0.0

    async def _play_audio_locally(self, text: str):
        """Original generate and play logic."""
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume, pitch=self.pitch)
        audio_stream = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_stream += chunk["data"]

        if not audio_stream: return
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_stream)
            tmp_path = tmp.name

        try:
            await asyncio.get_event_loop().run_in_executor(None, self._play_file, tmp_path)
        finally:
            try: os.unlink(tmp_path)
            except: pass

    def _play_file(self, path: str):
        """Synchronous pygame playback."""
        if not PYGAME_AVAILABLE: return
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)


# ── Standalone test ───────────────────────────────────────────────────────────

async def _test():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    agent = VoiceAgent(voice=DEFAULT_VOICE)
    agent.start()

    test_lines = [
        "Welcome to our live! We trade crypto and forex.",
        "To join our trading community, send us a direct message and we will get you started!",
        "We provide daily signals for Bitcoin, Ethereum, and top forex pairs.",
    ]

    for line in test_lines:
        print(f"Speaking: {line}")
        await agent.speak(line)
        await asyncio.sleep(0.5)

    # Wait for queue to drain
    await agent._queue.join()
    agent.stop()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(_test())