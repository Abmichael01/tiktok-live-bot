import asyncio
from TikTokLive import TikTokLiveClient
import json
import sys

async def debug_status(username):
    print(f"🔍 Debugging status for @{username}...")
    client = TikTokLiveClient(unique_id=f"@{username}")
    try:
        room_info = await client.retrieve_room_info()
        print("\n✅ RAW ROOM INFO RECEIVED:")
        print(json.dumps(room_info, indent=2) if isinstance(room_info, dict) else str(room_info))
        
        # Check standard live flags
        status = None
        room_id = None
        if isinstance(room_info, dict):
            status = room_info.get("status")
            room_id = room_info.get("room_id")
        else:
            status = getattr(room_info, "status", None)
            room_id = getattr(room_info, "room_id", None)
            
        print(f"\n📊 Extracted Data:")
        print(f" - Status: {status} (Type: {type(status)})")
        print(f" - Room ID: {room_id} (Type: {type(room_id)})")
        
        is_live = (str(status) == "2") or (room_id and str(room_id).isdigit() and int(room_id) > 0)
        print(f"\n✨ Verdict: {'LIVE 🟢' if is_live else 'OFFLINE 🔴'}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "urkelcodes"
    asyncio.run(debug_status(user))
