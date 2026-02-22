import subprocess
import sys
import os
import shutil
from pathlib import Path

# Paths to include in the bundle
# Format: (source_path, destination_name)
FILE_DATAS = [
    ("bot", "bot"),
    ("triggers.json", "."),
    ("voice.py", "."),
    ("icon.png", "."),
]

def build():
    print("Preparing build for TikTok Live Bot...")

    # Build data arguments for PyInstaller
    # Note: On Windows use ; as separator, on Linux use :
    sep = ";" if os.name == 'nt' else ":"
    data_args = []
    for src, dst in FILE_DATAS:
        if Path(src).exists():
            data_args.append(f"--add-data={src}{sep}{dst}")
        else:
            print(f"Warning: {src} not found, skipping...")

    # Build command
    icon_file = "icon.ico" if os.name == 'nt' else "icon.png"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "TikTokLiveBot",
        f"--icon={icon_file}" if Path(icon_file).exists() else "",
        # Automatically collect all PySide6 related files
        "--collect-all", "PySide6",
    ] + data_args + ["launcher.py"]
    
    # Filter out empty arguments if icon doesn't exist
    cmd = [arg for arg in cmd if arg]

    print(f"Running: {' '.join(cmd)}")
    
    # Use the venv's pyinstaller if possible
    venv_pyinstaller = Path(".venv/bin/pyinstaller")
    if os.name == 'nt':
        venv_pyinstaller = Path(".venv/Scripts/pyinstaller.exe")
    
    pyinst_path = str(venv_pyinstaller) if venv_pyinstaller.exists() else "pyinstaller"
    cmd[0] = pyinst_path

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("Icons generated successfully!")
        print(f"Output: dist/TikTokLiveBot{' .exe' if os.name == 'nt' else ''}")
    else:
        print("\nBuild failed.")

if __name__ == "__main__":
    build()
