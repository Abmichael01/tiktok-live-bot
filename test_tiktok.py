import asyncio
from TikTokLive import TikTokLiveClient
import json

async def main():
    try:
        client = TikTokLiveClient(unique_id="@urkelcodes")
        
        print(f"Fetching room info for {client.unique_id}...")
        info = await client.web.fetch_room_info(unique_id=client.unique_id)
        print(f"Info type: {type(info)}")
        
        status = info.get("status") if isinstance(info, dict) else getattr(info, "status", None)
        room_id = info.get("room_id") if isinstance(info, dict) else getattr(info, "room_id", None)
            
        print(f"Status: {status}, Room ID: {room_id}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
