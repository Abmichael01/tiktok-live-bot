import sys
import shutil
import os
from pathlib import Path

def get_base_path():
    """ Folder where the .exe or launcher.py lives """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent

def get_data_dir():
    """ Get a writable directory for user data (config, logs) """
    if getattr(sys, 'frozen', False):
        # On Windows, use %APPDATA%/TikTokLiveBot
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA')
            if appdata:
                data_path = Path(appdata) / "TikTokLiveBot"
                data_path.mkdir(parents=True, exist_ok=True)
                return data_path
    # In development or on non-Windows/non-frozen, use the base path
    return get_base_path()

def get_resource_path(relative_path):
    """ Get path to file bundled INSIDE the executable """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path

DATA_DIR = get_data_dir()
TRIGGERS_FILE = DATA_DIR / "triggers.json"
LOG_FILE = DATA_DIR / "bot_log.jsonl"

def ensure_config_exists():
    """ Copies bundled triggers.json to external DATA_DIR if it doesn't exist """
    if not TRIGGERS_FILE.exists():
        try:
            bundled_triggers = get_resource_path("triggers.json")
            if bundled_triggers.exists():
                # Ensure the destination directory exists (e.g. AppData folder)
                TRIGGERS_FILE.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(bundled_triggers, TRIGGERS_FILE)
                print(f"📦 Initialized default triggers at {TRIGGERS_FILE}")
        except Exception as e:
            print(f"⚠️ Could not initialize config: {e}")

# Initialize config on import
ensure_config_exists()

# Simli Ultra-Realistic Avatar Config
SIMLI_API_KEY = "er04arguoitpoer5v6i85"
SIMLI_FACE_ID = "9facea83-ad2d-45f4-8f68-9061937a67ca"
