import asyncio
import base64
import json
import logging
import cv2
import numpy as np
import pygame
import aiohttp
import sys
from simli import SimliClient, SimliConfig
from simli.simli import TransportMode

# Configuration - Loaded from bot.py's constants
SIMLI_API_KEY = "er04arguoitpoer5v6i85"
SIMLI_FACE_ID = "9facea83-ad2d-45f4-8f68-9061937a67ca"
WS_URL = "http://localhost:8765/ws"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("AvatarPC")

class SimliAvatarPC:
    def __init__(self):
        self.simli_client = None
        self._stop_event = asyncio.Event()

    async def start(self):
        # Initialize PyGame Mixer for audio output
        try:
            # Use small buffer to reduce latency
            pygame.mixer.init(frequency=48000, size=-16, channels=1, buffer=512)
            logger.info("PyGame Audio initialized (48kHz)")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            return

        # Initialize Simli
        config = SimliConfig(
            faceId=SIMLI_FACE_ID,
            handleSilence=True,
            maxSessionLength=3600 # 1 hour
        )
        
        # We switch to TransportMode.LIVEKIT (SFU mode) for better reliability
        self.simli_client = SimliClient(
            api_key=SIMLI_API_KEY,
            config=config,
            transport_mode=TransportMode.LIVEKIT
        )
        
        try:
            logger.info("Connecting to Simli servers...")
            await self.simli_client.start()
            logger.info("Simli Connection Established (SFU Mode)")
        except Exception as e:
            logger.error(f"Failed to start Simli Client: {e}")
            return

        # Start loops
        asyncio.create_task(self.video_render_loop())
        asyncio.create_task(self.audio_playback_loop())
        
        logger.info("PC Avatar is READY! (Press Q in the video window to stop)")
        
        await self.ws_loop()

    async def video_render_loop(self):
        try:
            async for frame in self.simli_client.getVideoStreamIterator(targetFormat='bgr24'):
                img = frame.to_ndarray()
                cv2.imshow("Simli Avatar PC", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self._stop_event.set()
                    break
        except Exception as e:
            logger.error(f"Video loop error: {e}")
        finally:
            cv2.destroyAllWindows()

    async def audio_playback_loop(self):
        try:
            async for audio_chunk in self.simli_client.getAudioStreamIterator(targetSampleRate=48000):
                # Play chunk via pygame
                sound = pygame.mixer.Sound(buffer=audio_chunk)
                sound.play()
        except Exception as e:
            logger.error(f"Audio loop error: {e}")

    async def ws_loop(self):
        while not self._stop_event.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(WS_URL) as ws:
                        logger.info(f"Connected to Bot WebSocket at {WS_URL}")
                        async for msg in ws:
                            if self._stop_event.is_set():
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("type") == "speaking":
                                    if data.get("status"):
                                        audio_b64 = data.get("audio")
                                        if audio_b64:
                                            audio_bytes = base64.b64decode(audio_b64)
                                            # Send to Simli
                                            await self.simli_client.send(audio_bytes)
                                    else:
                                        await self.simli_client.clearBuffer()
                                
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.warning(f"WebSocket connection lost, retrying in 2s... ({e})")
                    await asyncio.sleep(2)
                else:
                    break

    async def stop(self):
        self._stop_event.set()
        if self.simli_client:
            await self.simli_client.stop()
        pygame.mixer.quit()
        cv2.destroyAllWindows()
        logger.info("PC Avatar stopped")

if __name__ == "__main__":
    avatar = SimliAvatarPC()
    try:
        asyncio.run(avatar.start())
    except KeyboardInterrupt:
        asyncio.run(avatar.stop())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
