import sys
import os
import signal
import time
import asyncio
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt, QSize, QThread, QCoreApplication
from PySide6.QtGui import QIcon
from bot.main import TikTokChatBot

# Fix for standalone EXE plugin paths
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
    QCoreApplication.addLibraryPath(os.path.join(basedir, 'PySide6', 'plugins'))
    QCoreApplication.addLibraryPath(os.path.join(basedir, 'PySide6', 'Qt', 'plugins'))
    # Set the path for the webengine process as well
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.join(basedir, 'PySide6', 'QtWebEngineProcess.exe' if os.name == 'nt' else 'QtWebEngineProcess')

# Fix for Fontconfig error on some Linux distros
if os.name != 'nt':
    os.environ['FONTCONFIG_FILE'] = '/etc/fonts/fonts.conf'
    os.environ['QT_WEBENGINE_DISABLE_SANDBOX'] = '1'

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BotThread(QThread):
    def __init__(self, username, port):
        super().__init__()
        self.username = username
        self.port = port
        self.bot = None

    def run(self):
        # Run the bot in its own asyncio loop within this thread
        self.bot = TikTokChatBot(username=self.username, ws_port=self.port)
        asyncio.run(self.bot.run())

class WebViewWindow(QMainWindow):
    def __init__(self, title, url, width, height, is_vertical=False):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(QSize(width, height))
        self.resize(width, height)
        
        icon_path = get_resource_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        if is_vertical:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(url))
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        self.setCentralWidget(self.browser)

class TikTokStudioLauncher:
    def __init__(self, username, port=8765):
        self.username = username
        self.port = port
        self.bot_thread = None
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("TikTokLiveBot")
        
        # Windows taskbar icon fix
        if os.name == 'nt':
            try:
                import ctypes
                myappid = 'urkel.tiktokbot.studio.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass

        app_icon_path = get_resource_path("icon.png")
        if os.path.exists(app_icon_path):
            icon = QIcon(app_icon_path)
            self.app.setWindowIcon(icon)
            
        self.studio_win = None
        self.avatar_win = None

    def run(self):
        # Start bot in a background thread
        self.bot_thread = BotThread(self.username, self.port)
        self.bot_thread.start()
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Studio Dashboard
        self.studio_win = WebViewWindow(
            "TikTok Studio - Dashboard",
            f"http://localhost:{self.port}",
            1000, 700
        )
        self.studio_win.show()
        
        # Avatar View
        self.avatar_win = WebViewWindow(
            "Live Avatar",
            f"http://localhost:{self.port}/simli",
            360, 640,
            is_vertical=True
        )
        self.avatar_win.move(self.studio_win.x() + self.studio_win.width() + 20, self.studio_win.y())
        self.avatar_win.show()
        
        code = self.app.exec()
        self.cleanup()
        sys.exit(code)

    def cleanup(self):
        print("Stopping bot server...")
        if self.bot_thread:
            self.bot_thread.terminate()
            self.bot_thread.wait()

if __name__ == "__main__":
    launcher = TikTokStudioLauncher(username="urkelcodes")
    launcher.run()
