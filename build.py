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
    ("ffmpeg.exe", "."),
    ("ffprobe.exe", "."),
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
    
    # Dynamically find site-packages for deep scanning
    import site
    packages_path = site.getsitepackages()[0] if site.getsitepackages() else ""
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "TikTokLiveBot",
        f"--icon={icon_file}" if Path(icon_file).exists() else "",
        "--clean",
        # Force paths so CI finds the libs
        "--paths", packages_path,
        # Explicitly include PySide6 submodules
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtWebEngineCore",
        "--hidden-import", "PySide6.QtWebEngineWidgets",
        "--hidden-import", "PySide6.QtWebChannel",
        "--hidden-import", "PySide6.QtPrintSupport",
        "--hidden-import", "shiboken6",
        # Collect ALL files for major libs
        "--collect-all", "PySide6",
        "--collect-all", "shiboken6",
        "--collect-submodules", "PySide6",
        "--collect-all", "pygame",
        "--collect-all", "aiohttp",
        "--collect-all", "colorama",
    ] + data_args + ["launcher.py"]
    
    # Filter out empty arguments
    cmd = [arg for arg in cmd if arg]

    print(f"Running: {' '.join(cmd)}")
    
    # Use the venv's pyinstaller if possible, otherwise use system pyinstaller
    venv_pyinstaller = Path(".venv/Scripts/pyinstaller.exe") if os.name == 'nt' else Path(".venv/bin/pyinstaller")
    pyinst_path = str(venv_pyinstaller) if venv_pyinstaller.exists() else "pyinstaller"
    
    # In CI environments, always prefer the system path
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        pyinst_path = "pyinstaller"

    cmd[0] = pyinst_path

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\nBuild complete!")
        print(f"Output: dist/TikTokLiveBot{' .exe' if os.name == 'nt' else ''}")
    else:
        print("\nBuild failed.")

if __name__ == "__main__":
    build()
