import asyncio
import aiohttp
import json
import pygame
import sys
import random
import os

# Init Pygame
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TikTok Live VTuber Demo")

# Load Images
def load_image(filename):
    path = os.path.join(os.path.dirname(__file__), "assets", filename)
    if not os.path.exists(path):
        # Fallback to creating a colored surface
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.fill((255, 0, 0) if "talking" in filename else (0, 255, 0))
        return surf
    img = pygame.image.load(path)
    # Maintain aspect ratio loosely or scale
    img = pygame.transform.scale(img, (WIDTH, HEIGHT))
    return img

# Load Images
images = {
    "neutral": load_image("neutral.png"),
    "talking": load_image("talking.png"),
    "happy": load_image("happy.png"),
    "angry": load_image("angry.png"),
    "surprised": load_image("surprised.png"),
    "wave": load_image("wave.png")
}

# State
speaking = False
current_gesture = "neutral"

async def websocket_listener():
    global speaking, current_gesture
    url = "ws://localhost:8765/ws"
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    print(f"Connected to bot API at {url}")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("type") == "speaking":
                                speaking = data.get("status", False)
                                gesture = data.get("gesture", "neutral")
                                if gesture in images:
                                    current_gesture = gesture
                                else:
                                    current_gesture = "neutral"
                                    
                                if speaking:
                                    print(f"Speaking with gesture: {current_gesture}")
                                else:
                                    print("Stopped speaking")
        except Exception as e:
            print(f"WebSocket connection error: {e}. Retrying in 2s...")
            await asyncio.sleep(2)

async def main_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(websocket_listener())
    
    clock = pygame.time.Clock()
    
    flap_timer = 0
    flap_state = False # current state when speaking
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((0, 255, 0)) # Green screen background
        
        # Determine which image to show
        base_img = images.get(current_gesture, images["neutral"])
        
        if speaking:
            # Flap the mouth 
            flap_timer += clock.get_time()
            if flap_timer > 150: # toggle every 150ms
                flap_state = not flap_state
                flap_timer = 0
                
            if flap_state:
                # When talking, we show the talking mouth overlay or image
                # For now, we use the specific 'talking' image as the flap
                # But if we have a gesture, we might want to stay on that gesture?
                # Usually PNGTubers have "Talking" versions of every pose.
                # Since we only have ONE talking image, we'll swap to it.
                screen.blit(images["talking"], (0, 0))
            else:
                screen.blit(base_img, (0, 0))
        else:
            screen.blit(base_img, (0, 0))
            flap_state = False
            flap_timer = 0
            
        pygame.display.flip()
        
        # Free CPU for asyncio
        await asyncio.sleep(0.01)
        clock.tick(60)


if __name__ == "__main__":
    asyncio.run(main_loop())
