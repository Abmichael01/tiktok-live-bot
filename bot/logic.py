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
            
            # Ensure Simli settings exist with defaults
            if "simli_api_key" not in self.settings:
                self.settings["simli_api_key"] = "er04arguoitpoer5v6i85"
            if "simli_face_id" not in self.settings:
                self.settings["simli_face_id"] = "9facea83-ad2d-45f4-8f68-9061937a67ca"
            if "tiktok_username" not in self.settings:
                self.settings["tiktok_username"] = ""
            if "sign_server_url" not in self.settings:
                self.settings["sign_server_url"] = "https://w-sign.com/api/v1/sign" # Example default
                
            logger.info(f"{Fore.GREEN}✅ Loaded {len(self.triggers)} triggers")
        except FileNotFoundError:
            logger.error(f"{Fore.RED}❌ triggers.json not found")
            self.triggers = []
            self.settings = {}

    def save_config(self):
        with open(TRIGGERS_FILE, "w") as f:
            json.dump({"triggers": self.triggers, "settings": self.settings}, f, indent=2)
        logger.info(f"{Fore.CYAN}💾 Config saved")

    def match_comment(self, comment: str) -> Optional[dict]:
        case_sensitive = self.settings.get("case_sensitive", False)
        comment_check = comment if case_sensitive else comment.lower()

        for trigger in self.triggers:
            if not trigger.get("enabled", True): continue
            
            # Support both "keywords" (list) and "pattern" (string)
            keywords = trigger.get("keywords", [])
            pattern = trigger.get("pattern")
            
            if not keywords and pattern:
                keywords = [pattern]
                
            match_type = trigger.get("match_type", "any")
            matched = [kw for kw in keywords if (kw if case_sensitive else kw.lower()) in comment_check]

            if (match_type == "any" and matched) or (match_type == "all" and len(matched) == len(keywords)):
                return trigger
        return None

    def record_reply(self, uid: str):
        now = time.time()
        self.stats['total_replies'] += 1
        self.user_reply_times[uid].append(now)
        # Clean up old reply records
        self.user_reply_times[uid] = [t for t in self.user_reply_times[uid] if now - t < 300]
