# 🎵 TikTok Live Bot

A fully automated TikTok Live chatbot that reads live chat, auto-replies to viewer messages, and speaks replies out loud — all running hidden in the background.

---

## 🚀 Quick Start (Development)

```bash
# 1. Install everything
setup.bat

# 2. Run the launcher UI
python launcher.py
```

---

## 📦 Build the .exe (for client delivery)

```bash
# On Windows
python build.py
```

Delivers: `dist/TikTokLiveBot.exe`

---

## 📁 Files

| File | Purpose |
|---|---|
| `launcher.py` | Main entry point — the UI window |
| `bot.py` | Core bot — reads TikTok live chat |
| `commenter.py` | Playwright — hidden browser that posts comments |
| `voice.py` | edge-tts — speaks replies out loud |
| `triggers.json` | Keywords → replies config |
| `config.json` | Username + settings |
| `build.py` | Packages everything into .exe |
| `setup.bat` | One-time dependency installer |

---

## 🎯 How It Works

1. Client double-clicks `TikTokLiveBot.exe`
2. Enters their TikTok username and clicks Start
3. First run: browser opens for TikTok login → then hides
4. Bot connects to the live stream
5. When a viewer comments a trigger keyword:
   - Bot posts a text reply in the live chat
   - Bot speaks the reply out loud through PC speakers (into stream audio)
6. Dashboard at `http://localhost:8765` shows live stats and lets you manage triggers

---

## 🔑 Login

- First run opens a visible Chrome browser for login
- After login, browser hides and session is saved to `tiktok_session.json`
- Session lasts ~2 months
- Click "Re-login" in the app to refresh when it expires

---

## 🎯 Editing Triggers

Edit `triggers.json` directly or use the dashboard at `http://localhost:8765`.

---

## 🔊 Voice

Uses Microsoft edge-tts (free, no API key). Change the voice in `voice.py`:
- `en-US-GuyNeural` — Male American (default)
- `en-GB-RyanNeural` — Male British
- `en-US-JennyNeural` — Female American

---

## ⚠️ Notes

- The bot must be running while the live stream is active
- TikTok session cookie refreshes every ~2 months
- Keep `triggers.json` in the same folder as the exe
