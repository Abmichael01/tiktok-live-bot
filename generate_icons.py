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

    img = Image.open(img_path)
    
    # Generate .ico for Windows
    print("Generating icon.ico...")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("icon.ico", sizes=icon_sizes)
    
    # Generate .icns for macOS fallback
    print("Generating icon.icns...")
    img.save("icon.icns")
    
    print("Icons generated successfully!")

if __name__ == "__main__":
    generate_icons()
