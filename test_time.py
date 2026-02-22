import asyncio
import time
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

async def main():
    client = TikTokLiveClient(unique_id="@urkelcodes")

    @client.on(ConnectEvent)
    async def on_connect(event):
        print("Connected!")
        print("Current time.time():", time.time())

    @client.on(CommentEvent)
    async def on_comment(event):
        print(f"Comment from {event.user.nickname}: {event.comment}")
        print("base_message.create_time:", getattr(event.base_message, 'create_time', None))
        print("base_message.client_send_time:", getattr(event.base_message, 'client_send_time', None))
        
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
