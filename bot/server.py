import json
import asyncio
import aiohttp
import aiofiles
from aiohttp import web
from datetime import datetime
from colorama import Fore, Style
from bot.constants import DASHBOARD_HTML, TAVUS_HTML, LOG_FILE

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

    async def serve_tavus(self, request):
        return web.Response(text=TAVUS_HTML, content_type='text/html')

    async def create_tavus_session(self, request):
        api_key = self.bot.state.settings.get("tavus_api_key")
        replica_id = self.bot.state.settings.get("tavus_replica_id")
        persona_id = self.bot.state.settings.get("tavus_persona_id")

        if not api_key:
            return web.json_response({"error": "Missing Tavus API Key"}, status=400)

        url = "https://tavusapi.com/v2/conversations"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Following the user's provided documentation structure
        payload = {
            "persona_id": persona_id,
            "replica_id": replica_id, # Keep it if provided, but persona usually handles it
            "conversation_name": f"Market Mechanic Live - @{self.bot.username}",
            "properties": {
                "enable_recording": False,
                "enable_transcription": True
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 201:
                        text = await resp.text()
                        print(f"{Fore.RED}❌ Tavus API Error ({resp.status}): {text}{Style.RESET_ALL}")
                        return web.json_response({"error": f"Tavus API Error: {text}"}, status=resp.status)
                    data = await resp.json()
                    return web.json_response(data)
        except Exception as e:
            print(f"{Fore.RED}❌ Tavus Connection Exception: {str(e)}{Style.RESET_ALL}")
            return web.json_response({"error": str(e)}, status=500)

    async def log_event(self, event_type: str, data: dict):
        entry = {"timestamp": datetime.now().isoformat(), "type": event_type, **data}
        async with aiofiles.open(LOG_FILE, "a") as f:
            await f.write(json.dumps(entry) + "\n")
        await self.broadcast_ws(entry)
