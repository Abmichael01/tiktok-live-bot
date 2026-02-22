import asyncio
import base64
import json
import logging
import cv2
import numpy as np
import aiohttp
import sys
import time
import os

# Configuration
WS_URL = "http://localhost:8765/ws"
ASSETS_DIR = "assets"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("LocalAvatar")

class LocalAvatar:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self.is_speaking = False
        self.img_neutral = None
        self.img_talking = None
        self.window_name = "TikTok Bot - Local Avatar"

    async def start(self):
        # Load the images from assets
        self.img_neutral = cv2.imread(os.path.join(ASSETS_DIR, "neutral.png"))
        self.img_talking = cv2.imread(os.path.join(ASSETS_DIR, "talking.png"))
        
        if self.img_neutral is None:
            logger.error("❌ Could not find assets/neutral.png!")
            self.img_neutral = np.zeros((600, 400, 3), dtype=np.uint8)
            cv2.putText(self.img_neutral, "Missing assets", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        if self.img_talking is None:
            logger.warning("⚠️ assets/talking.png missing, using neutral for both.")
            self.img_talking = self.img_neutral

        logger.info("🚀 Local Avatar Window Opening...")
        asyncio.create_task(self.render_loop())
        await self.ws_loop()

    async def render_loop(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 400, 600)
        
        while not self._stop_event.is_set():
            # Switch image based on speaking status
            if self.is_speaking:
                # Rapidly switch between talking and neutral for "lip sync" effect
                if (int(time.time() * 8) % 2) == 0:
                    frame = self.img_talking.copy()
                else:
                    frame = self.img_neutral.copy()
                
                # Add a pulsing orange glow
                pulse = int(10 * np.sin(time.time() * 15)) + 10
                cv2.rectangle(frame, (0,0), (frame.shape[1], frame.shape[0]), (0, 165, 255), pulse)
            else:
                frame = self.img_neutral.copy()

            cv2.imshow(self.window_name, frame)
            
            if cv2.waitKey(30) & 0xFF == ord('q'):
                self._stop_event.set()
                break
            await asyncio.sleep(0.01)
        
        cv2.destroyAllWindows()

    async def ws_loop(self):
        while not self._stop_event.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(WS_URL) as ws:
                        logger.info(f"🔗 Connected to Bot at {WS_URL}")
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("type") == "speaking":
                                    self.is_speaking = data.get("status", False)
            except Exception as e:
                logger.warning(f"WebSocket Lost: {e}. Retrying...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    avatar = LocalAvatar()
    try:
        asyncio.run(avatar.start())
    except KeyboardInterrupt:
        pass
