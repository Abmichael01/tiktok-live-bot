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
        await self.bot.server.broadcast_ws({"type": "stats", "stats": state.stats})
        await self.bot.server.studio_log(f"{user}: {msg}", Fore.CYAN, type='comment', user_label='CHAT')
        await self.bot.server.log_event('comment', {'user': user, 'user_id': uid, 'comment': msg, 'replied': False})

        trigger = state.match_comment(msg)
        if trigger:
            await self.bot.reply_queue.put({'user': user, 'user_id': uid, 'comment': msg, 'trigger': trigger, 'response': trigger['response']})

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
