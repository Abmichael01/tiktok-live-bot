import time
import logging
from colorama import Fore
from TikTokLive.events import ConnectEvent, DisconnectEvent, CommentEvent, LikeEvent, GiftEvent, FollowEvent

logger = logging.getLogger("TikTokBot")

class BotEvents:
    def __init__(self, bot):
        self.bot = bot

    async def on_connect(self, event: ConnectEvent):
        self.bot.state.stats["connected"] = True
        self.bot.state.stats["live_status"] = "LIVE"
        self.bot.state.bot_start_time = time.time()
        await self.bot.server.studio_log(f"🟢 Connected to @{self.bot.username}", Fore.GREEN)
        await self.bot.server.broadcast_ws({
            "type": "status", 
            "connected": True, 
            "username": self.bot.username,
            "live_status": "LIVE"
        })
        
        # Trigger Automated Welcome Message
        welcome_text = """Most people are watching the charts right now and seeing a disaster.

Me? I’m seeing a massive, mechanical transfer of wealth.

Welcome to the stream. I’m your Market Mechanic.

While the panicked are selling, and the uneducated are getting liquidated... something else is happening behind the curtain. The big money? They aren't leaving. They’re positioning.

Today, we aren’t talking about 'hope' or 'vibes.' We’re talking about mechanics. We’re breaking down why the algorithms forced that 15% drop, why the 'Snapback' is mathematically inevitable, and how you can stop being the liquidity for someone else’s exit.

Drop your questions in the chat. Tell me what you're holding, and I'll tell you if you're holding a bag... or a golden ticket to the recovery.

Let’s get to work."""
        
        await self.bot.server.broadcast_ws({
            "type": "speaking",
            "status": True,
            "text": welcome_text,
            "user": "SYSTEM"
        })
        
        await self.bot.server.studio_log(f"🤖 WELCOME MESSAGE SENT", Fore.MAGENTA, type='reply')
        
    async def on_disconnect(self, event: DisconnectEvent):
        self.bot.state.stats["connected"] = False
        self.bot.state.stats["live_status"] = "OFFLINE"
        await self.bot.server.studio_log("🔴 Disconnected from live stream", Fore.YELLOW)
        await self.bot.server.broadcast_ws({
            "type": "status", 
            "connected": False,
            "live_status": "OFFLINE"
        })

    async def on_comment(self, event: CommentEvent):
        state = self.bot.state
        user = event.user.nickname or event.user.unique_id or 'Unknown'
        uid = str(event.user.unique_id or user)
        msg = event.comment or ''

        if state.bot_start_time == 0.0: return
        try:
            msg_time = float(event.base_message.create_time)
            # If the timestamp is in milliseconds (e.g. 13+ digits), convert to seconds
            if msg_time > 10000000000:
                msg_time /= 1000

            if msg_time < state.bot_start_time:
                return
        except Exception:
            pass

        if f'{uid}:{msg}' in state.seen_comment_ids: return
        state.seen_comment_ids.add(f'{uid}:{msg}')
        if len(state.seen_comment_ids) > 500: state.seen_comment_ids = set(list(state.seen_comment_ids)[100:])

        state.stats['total_comments'] += 1
        state.stats['total_replies'] += 1 # Every comment gets an AI response
        await self.bot.server.broadcast_ws({"type": "stats", "stats": state.stats})
        await self.bot.server.studio_log(f"{user}: {msg}", Fore.CYAN, type='comment', user_label='CHAT')
        await self.bot.server.log_event('comment', {'user': user, 'user_id': uid, 'comment': msg, 'replied': True})

        # Send directly to Tavus via WebSocket broadcast
        await self.bot.server.broadcast_ws({
            "type": "incoming_comment",
            "user": user,
            "comment": msg
        })

    async def on_like(self, event: LikeEvent):
        count = event.count if hasattr(event, 'count') else 1
        self.bot.state.stats["total_likes"] += count
        await self.bot.server.broadcast_ws({"type": "stats", "stats": self.bot.state.stats})
        user = event.user.nickname if event.user else "Someone"
        await self.bot.server.studio_log(f"❤️ {user} sent {count} likes!", Fore.MAGENTA)
        await self.bot.server.log_event("like", {"user": user, "count": count})

    async def on_gift(self, event: GiftEvent):
        self.bot.state.stats["total_gifts"] += 1
        await self.bot.server.broadcast_ws({"type": "stats", "stats": self.bot.state.stats})
        user = event.user.nickname if event.user else "Someone"
        gift = event.gift.name if hasattr(event, 'gift') and event.gift else "a gift"
        await self.bot.server.studio_log(f"🎁 {user} sent {gift}!", Fore.YELLOW)
        await self.bot.server.log_event("gift", {"user": user, "gift": gift})

    async def on_follow(self, event: FollowEvent):
        self.bot.state.stats["total_follows"] += 1
        await self.bot.server.broadcast_ws({"type": "stats", "stats": self.bot.state.stats})
        user = event.user.nickname if event.user else "Someone"
        await self.bot.server.studio_log(f"➕ {user} followed!", Fore.BLUE)
        await self.bot.server.log_event("follow", {"user": user})
