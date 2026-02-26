import asyncio
import time
import re
import logging
from datetime import datetime
from colorama import Fore

logger = logging.getLogger("TikTokBot")

class BotWorker:
    def __init__(self, bot):
        self.bot = bot

    async def reply_worker(self):
        logger.info(f'{Fore.CYAN}🔄 Reply worker started')
        while True:
            try:
                item = await self.bot.reply_queue.get()
                user, uid, msg, trigger, response = item['user'], item['user_id'], item['comment'], item['trigger'], item['response']

                self.bot.state.record_reply(uid)
                await self.bot.server.broadcast_ws({"type": "stats", "stats": self.bot.state.stats})
                await self.bot.server.studio_log(f"🤖 REPLY -> {user}: {response}", Fore.MAGENTA, type='reply')
                await self.bot.server.log_event('reply', {
                    'user': user, 
                    'user_id': uid, 
                    'trigger_id': trigger.get('id', trigger.get('pattern', 'unknown')), 
                    'matched_comment': msg, 
                    'response': response
                })

                if self.bot.voice_agent:
                    gesture = "neutral"
                    processed_response = response
                    match = re.search(r'^\[([a-zA-Z0-9]+)\]', response)
                    if match:
                        gesture = match.group(1).lower()
                        processed_response = response[match.end():].strip()
                    
                    speech_text = f"Replying to @{user}... {processed_response}"
                    await self.bot.voice_agent.speak(speech_text, gesture=gesture, metadata={"user": user})
                else:
                    # If local voice agent isn't used, broadcast to WebSocket for Tavus avatar
                    await self.bot.server.broadcast_ws({
                        "type": "speaking",
                        "status": True,
                        "text": f"Replying to @{user}... {response}",
                        "user": user,
                        "gesture": "neutral"
                    })

                self.bot.reply_queue.task_done()
                await asyncio.sleep(self.bot.state.settings.get('reply_cooldown_seconds', 3))
            except asyncio.CancelledError: break
            except Exception as e:
                logger.error(f'Reply worker error: {e}')
                await asyncio.sleep(2)

    async def perform_status_check(self):
        """Execute a single TikTok live status check."""
        from TikTokLive import TikTokLiveClient
        username = self.bot.username
        if not username: return
        
        sign_url = self.bot.state.settings.get("sign_server_url", "https://w-sign.com/api/v1/sign")
        client = TikTokLiveClient(
            unique_id=f"@{username}",
            web_kwargs={
                "signer_kwargs": {
                    "sign_api_base": sign_url
                }
            }
        )
        try:
            # Use the official is_live method with a timeout to prevent hanging
            is_live = await asyncio.wait_for(client.is_live(), timeout=15)
            status = "LIVE" if is_live else "OFFLINE"
            room_id = getattr(client, "room_id", "Unknown")
            
            # If the bot is already actively connected, it's definitely LIVE
            if self.bot.state.stats.get("connected"):
                is_live = True
                
            status_text = "LIVE" if is_live else "OFFLINE"
            
            self.bot.state.stats["live_status"] = status_text
            self.bot.state.stats["last_check"] = datetime.now().strftime("%H:%M:%S")
            
            if is_live:
                logger.info(f"{Fore.GREEN}📡 [Status] @{username} is LIVE ✓ (RoomID: {room_id})")
            else:
                logger.info(f"{Fore.YELLOW}📡 [Status] @{username} is OFFLINE (API Status: {status}, RoomID: {room_id})")
                
            await self.bot.server.broadcast_ws({
                "type": "status_update",
                "live_status": status_text,
                "last_check": self.bot.state.stats["last_check"]
            })
        except Exception as e:
            # Fallback: if bot is connected, trust that state
            if self.bot.state.stats.get("connected"):
                self.bot.state.stats["live_status"] = "LIVE"
                await self.bot.server.broadcast_ws({
                    "type": "status_update",
                    "live_status": "LIVE",
                    "last_check": datetime.now().strftime("%H:%M:%S")
                })
            else:
                logger.error(f"Status check failed for @{username}: {e}")

    async def poll_live_status(self):
        await asyncio.sleep(5) # Quick initial check
        while True:
            try:
                await self.perform_status_check()
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
            await asyncio.sleep(60)
