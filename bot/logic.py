import json
import time
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional, Dict, List, Set, Any
from colorama import Fore, Style

from bot.constants import TRIGGERS_FILE, LOG_FILE

logger = logging.getLogger("TikTokBot")

class BotState:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.triggers: List[Dict[str, Any]] = []
        self.settings: Dict[str, Any] = {}
        self.stats: Dict[str, Any] = {
            "total_comments": 0,
            "total_replies": 0,
            "total_likes": 0,
            "total_gifts": 0,
            "total_follows": 0,
            "start_time": datetime.now().isoformat(),
            "connected": False,
            "live_status": "OFFLINE",
            "last_check": None,
        }
        self.seen_comment_ids: Set[str] = set()
        self.user_reply_times: Dict[str, List[float]] = defaultdict(list)
        self.bot_start_time: float = 0.0
        self.running: bool = False

    def load_config(self):
        try:
            with open(TRIGGERS_FILE, "r") as f:
                self.config = json.load(f)
            self.triggers = self.config.get("triggers", [])
            self.settings = self.config.get("settings", {})
            
            if "tiktok_username" not in self.settings:
                self.settings["tiktok_username"] = ""
            if "sign_server_url" not in self.settings:
                self.settings["sign_server_url"] = "https://w-sign.com/api/v1/sign" # Example default
            if "tavus_api_key" not in self.settings:
                self.settings["tavus_api_key"] = "264f2cf5c17c4c819123e4814836829d"
            if "tavus_persona_id" not in self.settings:
                self.settings["tavus_persona_id"] = "pa290c2b7162"
            if "tavus_replica_id" not in self.settings:
                self.settings["tavus_replica_id"] = "rf4e9d9790f0"
                
            logger.info(f"{Fore.GREEN}✅ Loaded {len(self.triggers)} triggers")
        except FileNotFoundError:
            logger.error(f"{Fore.RED}❌ triggers.json not found")
            self.triggers = []
            self.settings = {}

    def save_config(self):
        with open(TRIGGERS_FILE, "w") as f:
            json.dump({"triggers": self.triggers, "settings": self.settings}, f, indent=2)
        logger.info(f"{Fore.CYAN}💾 Config saved")

    async def record_reply(self, uid: str):
        now = time.time()
        self.stats['total_replies'] += 1
        self.user_reply_times[uid].append(now)
        # Clean up old reply records
        self.user_reply_times[uid] = [t for t in self.user_reply_times[uid] if now - t < 300]
