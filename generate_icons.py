import sys
import os
from pathlib import Path
from PIL import Image

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def generate_icons():
    img_path = Path("icon.png")
    if not img_path.exists():
        print("icon.png not found!")
        return

    img = Image.open(img_path).convert("RGBA")
    
    # Process transparency: Replace black (0,0,0) with transparent (0,0,0,0)
    data = img.getdata()
    new_data = []
    for item in data:
        # If it's pure black or very close to black, make it transparent
        if item[0] < 15 and item[1] < 15 and item[2] < 15:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)

    # Autocrop: Remove empty transparent space around the icon
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        print("Cropped icon to content.")

    # Save processed PNG for browser/favicon
    img.save("icon.png")
    
    # Generate .ico for Windows
    print("Generating icon.ico...")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("icon.ico", sizes=icon_sizes)
    
    # Generate .icns for macOS fallback
    print("Generating icon.icns...")
    img.save("icon.icns")
    img.save("icon.icns")
    
    print("Icons generated successfully!")

if __name__ == "__main__":
    generate_icons()
