import json
import asyncio
import aiohttp
import aiofiles
from aiohttp import web
from datetime import datetime
from colorama import Fore, Style
from bot.constants import DASHBOARD_HTML, SIMLI_HTML, SIMLI_API_KEY, SIMLI_FACE_ID, LOG_FILE

class BotServer:
    def __init__(self, bot):
        self.bot = bot
        self.ws_clients = set()

    async def studio_log(self, msg, color=Fore.WHITE, type='info', user_label=None):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{ts}] {msg}{Style.RESET_ALL}")
        
        display_user = user_label
        if not display_user:
            display_user = "STUDIO" if type == "info" else "BOT"
            
        await self.broadcast_ws({
            "type": "comment" if type == "info" else type,
            "user": display_user,
            "comment": msg,
            "timestamp": ts
        })

    async def broadcast_ws(self, data: dict):
        if not self.ws_clients: return
        message = json.dumps(data)
        for ws in list(self.ws_clients):
            try:
                await ws.send_str(message)
            except:
                self.ws_clients.discard(ws)

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(max_msg_size=1024*1024*5)
        await ws.prepare(request)
        self.ws_clients.add(ws)
        try:
            await ws.send_str(json.dumps({
                "type": "init",
                "stats": self.bot.state.stats,
                "triggers": self.bot.state.triggers,
                "settings": self.bot.state.settings,
                "username": self.bot.username,
                "connected": self.bot.state.running,
            }))
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.bot.handle_command(ws, json.loads(msg.data))
        finally:
            self.ws_clients.discard(ws)
        return ws

    async def serve_dashboard(self, request):
        return web.Response(text=DASHBOARD_HTML, content_type='text/html')

    async def serve_simli(self, request):
        api_key = self.bot.state.settings.get("simli_api_key", SIMLI_API_KEY)
        face_id = self.bot.state.settings.get("simli_face_id", SIMLI_FACE_ID)
        html = SIMLI_HTML.replace("{{API_KEY}}", api_key).replace("{{FACE_ID}}", face_id)
        return web.Response(text=html, content_type='text/html')

    async def log_event(self, event_type: str, data: dict):
        entry = {"timestamp": datetime.now().isoformat(), "type": event_type, **data}
        async with aiofiles.open(LOG_FILE, "a") as f:
            await f.write(json.dumps(entry) + "\n")
        await self.broadcast_ws(entry)
