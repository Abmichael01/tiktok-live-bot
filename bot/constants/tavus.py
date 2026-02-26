TAVUS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Tavus Phoenix - Live Avatar</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@daily-co/daily-js"></script>
    <style>
        body, html {
            margin: 0; padding: 0; width: 100%; height: 100%;
            background-color: #00ff00; /* Chroma key */
            overflow: hidden; font-family: 'Quicksand', sans-serif;
        }
        #container {
            width: 100%; height: 100%; background: #000;
            position: relative; display: flex; justify-content: center; align-items: center;
        }
        #daily-call-frame {
            width: 100%; height: 100%; border: none;
        }
        #overlay-status {
            position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
            padding: 8px 16px; background: rgba(0,0,0,0.6); color: white;
            border-radius: 20px; font-size: 12px; backdrop-filter: blur(5px);
            z-index: 100; pointer-events: none; opacity: 0.8;
        }
        #reply-box {
            position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7); color: white; padding: 12px 24px;
            border-radius: 30px; font-size: 16px; font-weight: 600;
            backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.15);
            z-index: 200; text-align: center; max-width: 85%; transition: all 0.3s ease;
        }
        #reply-box.active {
            background: rgba(254, 44, 85, 0.9); border-color: rgba(254, 44, 85, 1);
            box-shadow: 0 8px 32px rgba(254,44,85,0.5);
        }
        #setup-screen {
            position: absolute; inset: 0; background: #111; z-index: 1000;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            color: white; text-align: center; padding: 40px;
        }
        .btn-ready {
            padding: 18px 40px; font-size: 20px; cursor: pointer;
            background: #fe2c55; color: white; border: none; border-radius: 50px;
            font-weight: bold; box-shadow: 0 10px 30px rgba(254,44,85,0.4);
            margin-top: 30px; font-family: 'Quicksand', sans-serif;
        }
        .btn-ready:disabled { background: #444; box-shadow: none; cursor: not-allowed; }
        #custom-alert-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85); backdrop-filter: blur(10px);
            z-index: 2000; display: none; justify-content: center; align-items: center;
        }
        .modal {
            background: #16161D; border: 1px solid #2C2C32; border-radius: 24px;
            padding: 32px; width: 340px; text-align: center;
            box-shadow: 0 20px 80px rgba(0,0,0,0.8);
            animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .modal-title { font-weight: 700; color: #fe2c55; margin-bottom: 12px; font-size: 18px; }
        .modal-msg { font-size: 14px; color: rgba(255,255,255,0.7); margin-bottom: 25px; line-height: 1.5; }
        .modal-btn { 
            width: 100%; padding: 12px; border-radius: 12px; border: none; 
            background: #fe2c55; color: white; font-weight: 700; cursor: pointer;
            font-family: 'Quicksand', sans-serif;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="setup-screen">
            <h1 style="margin-bottom: 10px;">Phoenix Model</h1>
            <p style="opacity: 0.6; font-size: 14px;">Initializing Tavus Real-Time Conversation...</p>
            <button id="start-btn" class="btn-ready">START PHOENIX AVATAR</button>
        </div>
        
        <div id="overlay-status">SYSTEM IDLE</div>
        <div id="reply-box">🎙️ Waiting for TikTok comments...</div>
        
        <div id="video-wrapper" style="width: 100%; height: 100%;"></div>

        <div id="custom-alert-overlay">
            <div class="modal">
                <div class="modal-title">System Alert</div>
                <div id="alert-msg" class="modal-msg"></div>
                <button class="modal-btn" onclick="closeAlert()">UNDERSTOOD</button>
            </div>
        </div>
    </div>

    <script>
        let callFrame = null;
        let ws = null;
        const startBtn = document.getElementById('start-btn');
        const setupScreen = document.getElementById('setup-screen');
        const statusEl = document.getElementById('overlay-status');
        const replyBox = document.getElementById('reply-box');

        function showAlert(msg) {
            document.getElementById('alert-msg').innerText = msg;
            document.getElementById('custom-alert-overlay').style.display = 'flex';
        }
        window.closeAlert = function() {
            document.getElementById('custom-alert-overlay').style.display = 'none';
        }

        async function initTavus() {
            startBtn.disabled = true;
            startBtn.innerText = "CREATING SESSION...";
            statusEl.innerText = "CREATING TAVUS SESSION...";

            try {
                // Request conversation URL from our backend
                const response = await fetch('/api/tavus/session', { method: 'POST' });
                const data = await response.json();
                
                if (data.error) throw new Error(data.error);
                if (!data.conversation_url) throw new Error("No conversation URL returned");

                statusEl.innerText = "JOINING WEBRTC ROOM...";
                
                callFrame = Daily.createFrame(document.getElementById('video-wrapper'), {
                    iframeStyle: {
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        border: '0',
                        zIndex: 1
                    },
                    showLeaveButton: false,
                    showFullscreenButton: false,
                    activeSpeakerMode: false,
                });

                await callFrame.join({ 
                    url: data.conversation_url,
                    userName: 'TikTok-Bot-Controller',
                    videoSource: false, // We don't need our camera
                    audioSource: false  // We don't need our mic (unless we want to talk back)
                });

                callFrame.on('app-message', (evt) => {
                    const msg = evt.data;
                    if (msg.event === 'conversation.replica.started_speaking') {
                        replyBox.classList.add('active');
                    } else if (msg.event === 'conversation.replica.stopped_speaking') {
                        replyBox.classList.remove('active');
                        replyBox.innerText = "🎙️ Listening to the chat...";
                    }
                });

                callFrame.on('joined-meeting', () => {
                    setupScreen.style.display = 'none';
                    statusEl.innerText = "PHOENIX ACTIVE";
                    initWebSocket();
                });

                callFrame.on('error', (e) => {
                    console.error("Daily Error:", e);
                    statusEl.innerText = "CONNECTION ERROR";
                    startBtn.disabled = false;
                    startBtn.innerText = "RETRY CONNECTION";
                    showAlert("Media Connection Error: Check your internet or browser permissions.");
                });

            } catch (err) {
                console.error(err);
                showAlert(err.message);
                startBtn.disabled = false;
                startBtn.innerText = "START PHOENIX AVATAR";
            }
        }

        function initWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // Handle comments from TikTok
                if (data.type === 'incoming_comment') {
                    replyBox.innerText = `🗣️ Thinking: "${data.comment}"`;
                    // Send to Tavus for AI response generation
                    if (callFrame) {
                        callFrame.sendAppMessage({
                            event: 'conversation.respond',
                            text: `[${data.user} says]: ${data.comment}`
                        }, '*');
                    }
                } 
                // Handle system messages (like the welcome intro)
                else if (data.type === 'speaking') {
                    if (data.status === true && data.text) {
                        replyBox.innerText = "🗣️ Speaking System Intro...";
                        if (callFrame) {
                            callFrame.sendAppMessage({
                                event: 'conversation.respond',
                                text: data.text
                            }, '*');
                        }
                    }
                }
            };

            ws.onclose = () => {
                statusEl.innerText = "WS DISCONNECTED";
                setTimeout(initWebSocket, 2000);
            };
        }

        startBtn.onclick = initTavus;
    </script>
</body>
</html>
"""
