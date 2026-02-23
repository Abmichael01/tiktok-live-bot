import asyncio
import json
import argparse
import sys
import logging
import time
from typing import Optional
from colorama import Fore
import aiohttp
from aiohttp import web
from TikTokLive import TikTokLiveClient

from bot.constants import LOG_FILE
from bot.logic import BotState
from bot.server import BotServer
from bot.events import BotEvents
from bot.worker import BotWorker

try:
    from voice import VoiceAgent
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TikTokBot")

class TikTokChatBot:
    def __init__(self, username: str, ws_port: int = 8765):
        self.username = username.lstrip("@")
        self.ws_port = ws_port
        self.state = BotState()
        self.state.load_config()
        self.server = BotServer(self)
        self.events = BotEvents(self)
        self.worker = BotWorker(self)
        self.client: Optional[TikTokLiveClient] = None
        self.reply_queue = asyncio.Queue()
        self.voice_agent: Optional["VoiceAgent"] = None

    async def start_tiktok(self):
        from TikTokLive.events import ConnectEvent, DisconnectEvent, CommentEvent, LikeEvent, GiftEvent, FollowEvent
        if self.state.running: return
        self.state.running = True
        
        # Configuration for custom signature server
        sign_url = self.state.settings.get("sign_server_url", "https://w-sign.com/api/v1/sign")
        
        await self.server.broadcast_ws({"type": "status", "connected": "connecting"})
        
        # Initialize client with custom session and sign server settings
        # In v6.x, custom sign server is passed via web_kwargs -> signer_kwargs
        self.client = TikTokLiveClient(
            unique_id=f"@{self.username}",
            web_kwargs={
                "signer_kwargs": {
                    "sign_api_base": sign_url
                }
            }
        )
        
        self.client.on(ConnectEvent)(self.events.on_connect)
        self.client.on(DisconnectEvent)(self.events.on_disconnect)
        self.client.on(CommentEvent)(self.events.on_comment)
        self.client.on(LikeEvent)(self.events.on_like)
        self.client.on(GiftEvent)(self.events.on_gift)
        self.client.on(FollowEvent)(self.events.on_follow)
        
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            await self.server.studio_log(f"🚀 Connecting to @{self.username} (Attempt {attempt}/{max_retries})...")
            try:
                await self.client.start()
                break # Success!
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    await self.server.studio_log(f"⚠️ Connection failed, retrying in 5s...", Fore.YELLOW)
                    await asyncio.sleep(5)
                else:
                    self.state.running = False
                    await self.server.studio_log(f"❌ Connection failed after {max_retries} attempts: {e}", Fore.RED)

    async def stop_tiktok(self):
        if not self.state.running: return
        self.state.running = False
        if self.client: await self.client.stop()
        await self.server.studio_log("🛑 TikTok connection stopped", Fore.YELLOW)

    async def handle_command(self, ws, data: dict):
        action = data.get("action")
        if action == "start_bot":
            user = data.get("username", "").lstrip("@")
            if user:
                self.username = user
                asyncio.create_task(self.start_tiktok())
        elif action == "stop_bot":
            asyncio.create_task(self.stop_tiktok())
        elif action == "check_status":
            user = data.get("username", "").lstrip("@")
            if user:
                self.username = user
            asyncio.create_task(self.worker.perform_status_check())
        elif action == "start_if_live":
            user = data.get("username", "").lstrip("@")
            if user:
                self.username = user
            asyncio.create_task(self._check_and_start(ws))
        elif action == "ping":
            await ws.send_str(json.dumps({"type": "pong", "stats": self.state.stats}))
        elif action == "save_settings":
            new_settings = data.get("settings", {})
            self.state.settings.update(new_settings)
            self.state.save_config()
            if not data.get("silent", False):
                await ws.send_str(json.dumps({"type": "settings_saved", "success": True}))
        elif action == "broadcast":
            # Repost message to all clients
            await self.server.broadcast_ws(data.get("payload", {}))

    async def _check_and_start(self, ws):
        try:
            sign_url = self.state.settings.get("sign_server_url", "https://w-sign.com/api/v1/sign")
            client = TikTokLiveClient(
                unique_id=f"@{self.username}",
                web_kwargs={
                    "signer_kwargs": {
                        "sign_api_base": sign_url
                    }
                }
            )
            is_live = await asyncio.wait_for(client.is_live(), timeout=15)
            if is_live:
                await ws.send_str(json.dumps({"type": "start_result", "success": True}))
                asyncio.create_task(self.start_tiktok())
            else:
                await ws.send_str(json.dumps({"type": "start_result", "success": False, "msg": f"@{self.username} is currently OFFLINE!"}))
        except Exception as e:
            await ws.send_str(json.dumps({"type": "start_result", "success": False, "msg": f"Error checking status: {str(e)}"}))

    async def run(self):
        if VOICE_AVAILABLE:
            async def on_speak_start(text, gesture, audio=None, metadata=None):
                await self.server.broadcast_ws({
                    "type": "speaking",
                    "status": True,
                    "text": text,
                    "gesture": gesture,
                    "audio": audio,
                    "user": metadata.get("user") if metadata else None
                })
            async def on_speak_stop():
                await self.server.broadcast_ws({
                    "type": "speaking",
                    "status": False
                })

            self.voice_agent = VoiceAgent(
                on_speak_start=on_speak_start,
                on_speak_stop=on_speak_stop
            )
            self.voice_agent.start()
            logger.info("🔊 Voice agent started")

        app = web.Application()
        app.router.add_get("/", self.server.serve_dashboard)
        app.router.add_get("/simli", self.server.serve_simli)
        from bot.constants.config import get_resource_path
        app.router.add_get("/favicon.ico", lambda r: web.FileResponse(get_resource_path("icon.png")))
        app.router.add_get("/ws", self.server.ws_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.ws_port)
        await site.start()
        
        logger.info(f"🚀 Studio Dashboard: http://localhost:{self.ws_port}")
        
        asyncio.create_task(self.worker.reply_worker())
        asyncio.create_task(self.worker.poll_live_status())
        
        while True: await asyncio.sleep(3600)

def main():
    parser = argparse.ArgumentParser(description="TikTok Live Chat Bot")
    parser.add_argument("--username", "-u", required=True)
    parser.add_argument("--port", "-p", type=int, default=8765)
    args = parser.parse_args()

    bot = TikTokChatBot(username=args.username, ws_port=args.port)
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")

if __name__ == "__main__":
    main()
