SIMLI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Live Bot - Avatar</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body, html {
            margin: 0; padding: 0; width: 100%; height: 100%;
            background-color: #00ff00; /* Standard chroma key green */
            overflow: hidden; display: flex;
            justify-content: center; align-items: center;
            font-family: 'Quicksand', sans-serif;
        }
        #simli-container {
            width: 100%; height: 100%;
            background: #000;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #simli-video { 
            width: 100%;
            height: 100%;
            object-fit: cover; /* This makes it fill the vertical space */
        }
        #reply-box {
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            cursor: grab;
            user-select: none;
            transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
            z-index: 500;
            max-width: 85%;
            text-align: center;
        }
        #reply-box:active {
            cursor: grabbing;
        }
        #reply-box.active {
            background: rgba(254, 44, 85, 0.9); /* TikTok red */
            border-color: rgba(254, 44, 85, 1);
            box-shadow: 0 8px 32px rgba(254,44,85,0.5);
        }
        #status {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            color: white; font-family: 'Quicksand', sans-serif; font-size: 10px;
            background: rgba(0,0,0,0.5); padding: 4px 10px; border-radius: 20px;
            pointer-events: none; opacity: 0.5;
        }
        #start-overlay {
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8); z-index: 1000;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
        }
        #start-btn {
            padding: 15px 30px; font-size: 18px; cursor: pointer;
            background: #fe2c55; color: white; border: none; border-radius: 50px;
            font-weight: bold; box-shadow: 0 4px 20px rgba(254,44,85,0.4);
            font-family: 'Quicksand', sans-serif;
        }
    </style>
</head>
<body>
    <div id="simli-container">
        <div id="reply-box">🎙️ Ask me any question about the market...</div>
        <div id="status">Waiting for interaction...</div>
        <div id="start-overlay">
            <button id="start-btn">READY TO TELECAST</button>
        </div>
        <video id="simli-video" autoplay playsinline></video>
        <audio id="simli-audio" autoplay></audio>
    </div>

    <script type="module">
        import { SimliClient, generateSimliSessionToken } from 'https://esm.sh/simli-client';

        const statusElement = document.getElementById('status');
        const startBtn = document.getElementById('start-btn');
        const overlay = document.getElementById('start-overlay');
        const videoElement = document.getElementById('simli-video');
        const audioElement = document.getElementById('simli-audio');
        let simliClient;

        async function initSimli() {
            try {
                statusElement.innerText = "Requesting session...";
                const res = await generateSimliSessionToken({
                    apiKey: "{{API_KEY}}",
                    config: { faceId: "{{FACE_ID}}", handleSilence: true }
                });
                
                simliClient = new SimliClient(res.session_token, videoElement, audioElement, null, 0, "livekit");
                
                simliClient.on('start', () => {
                    statusElement.innerText = "";
                    statusElement.style.display = 'none';
                    overlay.style.display = 'none';
                });

                simliClient.on('error', (err) => { statusElement.innerText = "Error: " + err; });

                await simliClient.start();
            } catch (error) {
                statusElement.innerText = "Init Failed: " + error.message;
            }
        }

        function connectBot() {
            const replyBox = document.getElementById('reply-box');
            let isDragging = false;
            let currentX;
            let currentY;
            let initialX;
            let initialY;
            let xOffset = 0;
            let yOffset = 0;

            replyBox.addEventListener('mousedown', (e) => {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
                isDragging = true;
                replyBox.style.transition = 'none'; // Smooth drag
            });
            document.addEventListener('mouseup', () => {
                isDragging = false;
                replyBox.style.transition = 'background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease';
            });
            document.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    e.preventDefault();
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                    xOffset = currentX;
                    yOffset = currentY;
                    replyBox.style.transform = `translate(calc(-50% + ${currentX}px), ${currentY}px)`;
                }
            });

            const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'speaking') {
                    if (data.status === true) {
                        if (data.user) {
                            replyBox.innerText = `🗣️ Replying to @${data.user}...`;
                            replyBox.classList.add('active');
                        } else {
                            replyBox.innerText = "🗣️ Speaking...";
                            replyBox.classList.add('active');
                        }
                        if (simliClient && data.audio) {
                            const binaryString = atob(data.audio);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
                            simliClient.sendAudioData(bytes);
                        }
                    } else {
                        // Stop speaking
                        replyBox.innerText = "🎙️ Ask me any question about the market...";
                        replyBox.classList.remove('active');
                    }
                }
            };
            ws.onclose = () => setTimeout(connectBot, 2000);
        }
        
        // Connect WebSocket immediately
        connectBot();

        startBtn.onclick = () => {
            startBtn.innerText = "Connecting...";
            startBtn.disabled = true;
            initSimli();
        };
    </script>
</body>
</html>
"""
