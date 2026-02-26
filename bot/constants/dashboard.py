DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Live Bot</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #FE2C55;
            --secondary: #25F4EE;
            --bg: #0B0B0E;
            --card: #16161D;
            --surface: #1E1E26;
            --text: #FFFFFF;
            --text-dim: #8E8E93;
            --border: #2C2C32;
            --glow: rgba(254, 44, 85, 0.4);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Quicksand', sans-serif;
            background-color: var(--bg); color: var(--text); overflow: hidden;
            display: flex; flex-direction: column; height: 100vh;
        }
        header {
            padding: 12px 24px; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(22, 22, 29, 0.8); backdrop-filter: blur(20px);
            z-index: 100;
        }
        .logo { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }
        .logo span { background: linear-gradient(90deg, var(--primary), #FF4D6D); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        .status-pill {
            display: flex; align-items: center; gap: 8px; padding: 4px 12px;
            background: rgba(255,255,255,0.05); border-radius: 100px; border: 1px solid var(--border);
            font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
        }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #444; }
        .status-dot.online { background: var(--secondary); box-shadow: 0 0 10px var(--secondary); animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

        .tabs { display: flex; background: var(--card); border-bottom: 1px solid var(--border); padding: 0 20px; }
        .tab { 
            padding: 14px 20px; cursor: pointer; border-bottom: 2px solid transparent; 
            color: var(--text-dim); font-weight: 600; font-size: 13px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .tab.active { color: var(--text); border-bottom-color: var(--primary); text-shadow: 0 0 10px var(--glow); }
        .tab:hover { color: var(--text); background: rgba(255,255,255,0.03); }

        main { flex: 1; overflow: hidden; position: relative; }
        .page { display: none; height: 100%; width: 100%; padding: 24px; overflow-y: auto; opacity: 0; transform: translateY(10px); transition: all 0.3s ease; }
        .page.active { display: block; opacity: 1; transform: translateY(0); }

        #live-lock-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(11, 11, 14, 0.85); backdrop-filter: blur(12px);
            z-index: 500; display: flex; flex-direction: column; justify-content: center; align-items: center;
            opacity: 0; pointer-events: none; transition: all 0.5s ease;
        }
        #live-lock-overlay.active { opacity: 1; pointer-events: all; }
        .lock-card {
            background: var(--card); border: 1px solid var(--border); border-radius: 24px;
            padding: 40px; text-align: center; max-width: 400px;
            box-shadow: 0 20px 80px rgba(0,0,0,0.5);
            transform: scale(0.9); transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        #live-lock-overlay.active .lock-card { transform: scale(1); }
        .lock-icon { font-size: 48px; margin-bottom: 20px; animation: float 3s infinite ease-in-out; }
        @keyframes float { 0% { transform: translateY(0); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0); } }
        .lock-title { font-size: 24px; font-weight: 700; margin-bottom: 12px; }
        .lock-desc { font-size: 14px; color: var(--text-dim); line-height: 1.6; margin-bottom: 30px; }

        #custom-alert-overlay, #confirm-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); backdrop-filter: blur(8px);
            z-index: 2000; display: none; justify-content: center; align-items: center;
        }
        .modal {
            background: var(--card); border: 1px solid var(--border); border-radius: 24px;
            padding: 32px; width: 360px; text-align: center;
            box-shadow: 0 20px 80px rgba(0,0,0,0.8);
            animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .settings-form { max-width: 600px; display: flex; flex-direction: column; gap: 20px; }
        .field-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 13px; font-weight: bold; color: var(--text-dim); }
        input[type="text"] {
            background: var(--surface); border: 1px solid var(--border); color: white;
            padding: 10px 16px; border-radius: 10px; font-size: 14px; outline: none;
            font-family: 'Quicksand', sans-serif; transition: border-color 0.2s;
        }
        input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--glow); }

        .dashboard-grid { display: grid; grid-template-columns: 1fr 280px; gap: 20px; height: calc(100% - 80px); }
        .panel { background: var(--card); border-radius: 16px; border: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }
        .panel-header { padding: 12px 20px; border-bottom: 1px solid var(--border); font-size: 11px; font-weight: 800; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
        .log-container { flex: 1; padding: 16px; font-family: "SF Mono", monospace; font-size: 12px; overflow-y: auto; color: #E0E0E0; }
        .log-entry { margin-bottom: 6px; }
        .log-ts { color: var(--text-dim); margin-right: 10px; font-size: 10px; }
        .log-comment { color: var(--secondary); }
        .log-bot { color: var(--primary); font-weight: 600; }

        .stats-list { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
        .stat-item { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }
        .stat-label { color: var(--text-dim); font-size: 12px; }
        .stat-value { font-weight: 700; font-size: 20px; }

        .guide-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 10px; }
        .guide-card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 24px; position: relative; }
        .step-badge { background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; margin-bottom: 15px; }
        .guide-card h3 { font-size: 16px; margin-bottom: 10px; }
        .guide-card p { font-size: 13px; color: var(--text-dim); line-height: 1.6; }
        .guide-tip { margin-top: 15px; padding: 10px; background: rgba(254, 44, 85, 0.1); border-radius: 8px; font-size: 11px; color: var(--primary); }

        button {
            padding: 10px 20px; border-radius: 10px; border: none; font-weight: 700;
            cursor: pointer; transition: all 0.2s; font-size: 13px; display: flex; align-items: center; gap: 8px;
            font-family: 'Quicksand', sans-serif;
        }
        .btn-primary { background: var(--primary); color: white; box-shadow: 0 4px 15px var(--glow); }
        .btn-secondary { background: var(--surface); color: white; border: 1px solid var(--border); }
        .btn-secondary:hover { background: #2C2C35; }
    </style>
</head>
<body>
    <header>
        <div class="logo"><span>TikTok</span> Live Bot</div>
        <div class="status-pill">
            <div id="status-dot" class="status-dot"></div>
            <span id="status-text">OFFLINE</span>
        </div>
    </header>

    <div class="tabs">
        <div class="tab active" onclick="showPage('telecast', this)">TELECAST</div>
        <div class="tab" onclick="showPage('guide', this)">SETUP GUIDE</div>
        <div class="tab" onclick="showPage('settings', this)">SETTINGS</div>
    </div>

    <main>
        <div id="telecast" class="page active">
            <div id="live-lock-overlay" class="active">
                <div class="lock-card">
                    <div class="lock-icon">🤖</div>
                    <div class="lock-title">Launch Bot</div>
                    <div class="lock-desc">Enter your TikTok username to verify and connect.</div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <input type="text" id="username-input-lock" placeholder="@username" style="width:100%; text-align:center;">
                        <button class="btn-primary" id="btn-start-bot" onclick="attemptStartBot()" style="width:100%; justify-content:center;">START BOT</button>
                        <div id="lock-status" style="font-size: 11px; color: var(--primary); min-height: 16px;"></div>
                    </div>
                </div>
            </div>
            
            <div style="display:flex; justify-content:flex-end; padding-bottom: 12px;">
                <button id="stop-btn" class="btn-secondary" style="display:none;">🛑 STOP BOT</button>
            </div>
            
            <div class="dashboard-grid">
                <div class="panel">
                    <div class="panel-header">Activity Log</div>
                    <div id="log-window" class="log-container"></div>
                </div>
                <div class="panel">
                    <div class="panel-header">Session Stats</div>
                    <div class="stats-list">
                        <div class="stat-item"><span class="stat-label">Comments</span><span id="stat-comments" class="stat-value">0</span></div>
                        <div class="stat-item"><span class="stat-label">Replies</span><span id="stat-replies" class="stat-value">0</span></div>
                        <div class="stat-item"><span class="stat-label">Likes</span><span id="stat-likes" class="stat-value">0</span></div>
                        <div class="stat-item"><span class="stat-label">Gifts</span><span id="stat-gifts" class="stat-value">0</span></div>
                    </div>
                </div>
            </div>
        </div>

        <div id="guide" class="page">
            <h2 style="margin-bottom: 8px;">Setup Guide</h2>
            <p style="color: var(--text-dim); font-size: 14px; margin-bottom: 30px;">Follow these 4 simple steps to go live.</p>
            
            <div class="guide-steps">
                <div class="guide-card">
                    <div class="step-badge">1</div>
                    <h3>Launch Avatar</h3>
                    <p>Open the standalone Avatar window. It has a built-in green screen for TikTok Studio.</p>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button onclick="window.open('/tavus', '_blank', 'width=360,height=640')" class="btn-primary" style="width:100%; justify-content: center; background: #25F4EE; color: #000; box-shadow: 0 4px 15px rgba(37, 244, 238, 0.3);">OPEN PHOENIX AVATAR</button>
                    </div>
                </div>

                <div class="guide-card">
                    <div class="step-badge">2</div>
                    <h3>Add Source</h3>
                    <p>In TikTok Live Studio, add a <b>Window Capture</b> source and select the Avatar window.</p>
                    <div class="guide-tip">Make sure the Avatar window is not minimized!</div>
                </div>

                <div class="guide-card">
                    <div class="step-badge">3</div>
                    <h3>Apply Chroma Key</h3>
                    <p>Right-click the source in Studio -> Filters -> Add <b>Chroma Key</b>. Select the green background.</p>
                </div>

                <div class="guide-card">
                    <div class="step-badge">4</div>
                    <h3>Audio Mix</h3>
                    <p>The AI voice plays through your browser. Ensure <b>System Audio</b> is on in TikTok Studio.</p>
                </div>
            </div>
        </div>

        <div id="settings" class="page">
            <div class="settings-form">
                <div class="field-group">
                    <label>TikTok Username</label>
                    <input type="text" id="tiktok-username" placeholder="@your-username">
                </div>
                <div class="field-group">
                    <label>Signature Server (Custom)</label>
                    <input type="text" id="sign-server-url" placeholder="https://...">
                    <div style="font-size: 10px; color: var(--text-dim); margin-top: 4px;">Use this if you encounter connection errors or are in a restricted region.</div>
                </div>
                <div style="padding: 15px; background: rgba(37, 244, 238, 0.05); border: 1px solid rgba(37, 244, 238, 0.1); border-radius: 12px; margin-top: 5px;">
                    <h4 style="font-size: 12px; color: var(--secondary); margin-bottom: 12px; text-transform: uppercase;">Tavus Phoenix Configuration</h4>
                    <div class="field-group" style="margin-bottom: 15px;">
                        <label>Tavus API Key</label>
                        <input type="text" id="tavus-api-key" placeholder="Enter Tavus Key">
                    </div>
                    <div class="field-group" style="margin-bottom: 15px;">
                        <label>Tavus Persona ID</label>
                        <input type="text" id="tavus-persona-id" placeholder="Enter Persona ID">
                    </div>
                    <div class="field-group">
                        <label>Tavus Replica ID</label>
                        <input type="text" id="tavus-replica-id" placeholder="Enter Replica ID">
                    </div>
                </div>
                <div class="field-group">
                    <label>Avatar Dimensions (Portrait: 360x640)</label>
                    <div style="display:flex; gap:10px;">
                        <input type="text" id="av-width" value="360" style="flex:1;">
                        <input type="text" id="av-height" value="640" style="flex:1;">
                    </div>
                </div>
                <button onclick="saveSettings()" class="btn-primary" style="align-self: flex-start;">SAVE SETTINGS</button>
            </div>
        </div>
    </main>

    <div id="custom-alert-overlay">
        <div class="modal">
            <div id="alert-title" style="font-weight:700; color:var(--primary); margin-bottom:10px;">Alert</div>
            <div id="alert-msg" style="font-size:14px; color:var(--text-dim); margin-bottom:20px;"></div>
            <button class="btn-primary" onclick="closeAlert()" style="width:100%; justify-content:center;">OK</button>
        </div>
    </div>

    <div id="confirm-overlay">
        <div class="modal">
            <h3 style="margin-bottom: 12px;">Save Changes?</h3>
            <p style="font-size: 14px; color: var(--text-dim); margin-bottom: 24px;">This will update your bot configuration. Proceed?</p>
            <div style="display:flex; gap:12px;">
                <button class="btn-secondary" onclick="closeConfirm()" style="flex:1; justify-content:center;">CANCEL</button>
                <button class="btn-primary" onclick="processSaveSettings()" style="flex:1; justify-content:center;">YES, SAVE</button>
            </div>
        </div>
    </div>

    <script>
        let ws;
        function connect() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'init') {
                    updateStats(data.stats);
                    updateUIStatus(data.connected);
                    if (data.settings) {
                        document.getElementById('tiktok-username').value = data.settings.tiktok_username || "";
                        document.getElementById('sign-server-url').value = data.settings.sign_server_url || "";
                        document.getElementById('tavus-api-key').value = data.settings.tavus_api_key || "";
                        document.getElementById('tavus-persona-id').value = data.settings.tavus_persona_id || "";
                        document.getElementById('tavus-replica-id').value = data.settings.tavus_replica_id || "";
                        document.getElementById('username-input-lock').value = data.settings.tiktok_username || "";
                    }
                } else if (data.type === 'settings_saved') {
                    showAlert("Success", "Settings saved!");
                } else if (data.type === 'start_result') {
                    const btn = document.getElementById('btn-start-bot');
                    btn.innerText = 'START BOT'; btn.disabled = false;
                    if (!data.success) {
                        showAlert("Error", data.msg);
                    } else {
                        // Success! Bot is connected to TikTok.
                        // Now the user can manually open and start the avatar.
                    }
                } else if (data.type === 'status') {
                    updateUIStatus(data.connected);
                } else if (data.type === 'stats') {
                    updateStats(data.stats);
                } else if (data.type === 'comment') {
                    appendLog('comment', `💬 ${data.user}: ${data.comment}`);
                } else if (data.type === 'reply') {
                    appendLog('bot', data.comment);
                }
            };
            ws.onclose = () => setTimeout(connect, 2000);
        }

        function attemptStartBot() {
            const user = document.getElementById('username-input-lock').value.trim();
            if (!user) return showAlert("Error", "Please enter a username.");
            const btn = document.getElementById('btn-start-bot');
            btn.innerText = 'CHECKING...'; btn.disabled = true;
            
            // Save username to settings silently
            ws.send(JSON.stringify({ 
                action: 'save_settings', 
                silent: true,
                settings: { tiktok_username: user } 
            }));
            
            ws.send(JSON.stringify({ action: 'start_if_live', username: user }));
        }

        function showAlert(title, msg) {
            document.getElementById('alert-title').innerText = title;
            document.getElementById('alert-msg').innerText = msg;
            document.getElementById('custom-alert-overlay').style.display = 'flex';
        }
        function closeAlert() { document.getElementById('custom-alert-overlay').style.display = 'none'; }
        
        function saveSettings() { document.getElementById('confirm-overlay').style.display = 'flex'; }
        function closeConfirm() { document.getElementById('confirm-overlay').style.display = 'none'; }
        
        function processSaveSettings() {
            closeConfirm();
            ws.send(JSON.stringify({ 
                action: 'save_settings', 
                settings: {
                    tiktok_username: document.getElementById('tiktok-username').value.trim(),
                    sign_server_url: document.getElementById('sign-server-url').value.trim(),
                    tavus_api_key: document.getElementById('tavus-api-key').value.trim(),
                    tavus_persona_id: document.getElementById('tavus-persona-id').value.trim(),
                    tavus_replica_id: document.getElementById('tavus-replica-id').value.trim()
                }
            }));
        }

        function updateUIStatus(status) {
            const dot = document.getElementById('status-dot');
            const text = document.getElementById('status-text');
            const overlay = document.getElementById('live-lock-overlay');
            const stopBtn = document.getElementById('stop-btn');
            
            if (status === true || status === 'true') {
                dot.classList.add('online'); text.innerText = 'CONNECTED';
                overlay.classList.remove('active'); stopBtn.style.display = 'flex';
            } else if (status === 'connecting') {
                dot.style.background = '#FFB800'; text.innerText = 'CONNECTING';
                overlay.classList.remove('active');
            } else {
                dot.classList.remove('online'); dot.style.background = '#444'; text.innerText = 'OFFLINE';
                overlay.classList.add('active'); stopBtn.style.display = 'none';
            }
        }

        function updateStats(stats) {
            if (!stats) return;
            document.getElementById('stat-comments').innerText = stats.total_comments || 0;
            document.getElementById('stat-replies').innerText = stats.total_replies || 0;
            document.getElementById('stat-likes').innerText = stats.total_likes || 0;
            document.getElementById('stat-gifts').innerText = stats.total_gifts || 0;
        }

        function appendLog(type, msg) {
            const win = document.getElementById('log-window');
            if(!win) return;
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const ts = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'});
            entry.innerHTML = `<span class="log-ts">${ts}</span><span class="log-${type}">${msg}</span>`;
            win.appendChild(entry); win.scrollTop = win.scrollHeight;
        }

        function showPage(id, tabEl) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            if (tabEl) tabEl.classList.add('active');
        }

        document.getElementById('stop-btn').onclick = () => ws.send(JSON.stringify({ action: 'stop_bot' }));
        connect();
    </script>
</body>
</html>
"""
