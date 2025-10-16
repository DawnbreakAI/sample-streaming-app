"""
Flask Real-Time Audio Transcription App with Backend Authentication
Uses your existing /login API at http://127.0.0.1:8000/login

Features:
- Backend authentication via your login API
- Automatic token refresh every 55 minutes
- Real-time transcription
- Improved audio capture
"""

from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Voice Transcription (Authenticated)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 900px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        
        /* Auth Section */
        .auth-section {
            background: #f0f9ff;
            border: 2px solid #3b82f6;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .auth-section.authenticated {
            background: #f0fdf4;
            border-color: #10b981;
        }
        
        .auth-section.error {
            background: #fef2f2;
            border-color: #ef4444;
        }
        
        .auth-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .auth-status {
            font-weight: 600;
            font-size: 14px;
        }
        
        .user-info {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .auth-form {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .auth-form input {
            flex: 1;
            min-width: 200px;
            padding: 10px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .auth-form input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        /* Token Info */
        .token-info {
            background: #fffbeb;
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            font-size: 13px;
        }
        
        .token-info.hidden {
            display: none;
        }
        
        .token-status {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .refresh-indicator {
            color: #10b981;
            font-weight: 600;
        }
        
        /* Controls */
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 15px 30px;
            font-size: 16px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-login {
            background: #3b82f6;
            color: white;
        }
        
        .btn-login:hover:not(:disabled) {
            background: #2563eb;
        }
        
        .btn-login.loading {
            background: #93c5fd;
        }
        
        .btn-logout {
            background: #ef4444;
            color: white;
            padding: 10px 20px;
            font-size: 14px;
        }
        
        .btn-logout:hover:not(:disabled) {
            background: #dc2626;
        }
        
        #startBtn {
            background: #10b981;
            color: white;
        }
        
        #startBtn:hover:not(:disabled) {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
        }
        
        #stopBtn {
            background: #ef4444;
            color: white;
        }
        
        #stopBtn:hover:not(:disabled) {
            background: #dc2626;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
        }
        
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 600;
        }
        
        .status.idle {
            background: #f3f4f6;
            color: #6b7280;
        }
        
        .status.recording {
            background: #fef3c7;
            color: #92400e;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .status.processing {
            background: #dbeafe;
            color: #1e40af;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .transcription-box {
            background: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 20px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .transcription-item {
            margin-bottom: 15px;
            padding: 12px;
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 5px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .chunk-label {
            font-size: 12px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .chunk-text {
            color: #333;
            line-height: 1.6;
        }
        
        .final-transcription {
            background: #f0fdf4;
            border: 2px solid #10b981;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .final-label {
            color: #10b981;
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
        }
        
        .final-text {
            color: #333;
            line-height: 1.8;
            font-size: 16px;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            padding: 15px;
            background: #f3f4f6;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 5px;
        }
        
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .debug-log {
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 5px;
            padding: 10px;
            margin-top: 20px;
            max-height: 150px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 11px;
            color: #4b5563;
        }
        
        .info-banner {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 5px;
            font-size: 13px;
            color: #1e40af;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Real-Time Voice Transcription</h1>
        <p class="subtitle">Authenticated with Automatic Token Refresh</p>
        
        <!-- Info Banner -->
        <div class="info-banner">
            <strong>🔐 Secure Session:</strong> Your session is authenticated and tokens will automatically refresh every 55 minutes. You can record for hours without interruption!
        </div>
        
        <!-- Authentication Section -->
        <div id="authSection" class="auth-section">
            <div class="auth-header">
                <div class="auth-status" id="authStatus">🔒 Not Authenticated</div>
                <button id="logoutBtn" class="btn-logout" style="display: none;">Logout</button>
            </div>
            <div class="user-info" id="userInfo" style="display: none;"></div>
            
            <form id="loginForm" class="auth-form">
                <input type="email" id="emailInput" placeholder="Email" required>
                <input type="password" id="passwordInput" placeholder="Password" required>
                <button type="submit" class="btn-login" id="loginBtn">
                    <span id="loginBtnText">🔑 Login</span>
                </button>
            </form>
        </div>
        
        <!-- Token Info -->
        <div id="tokenInfo" class="token-info hidden">
            <div class="token-status">
                <span>🔄 Auto-refresh: <span class="refresh-indicator" id="refreshStatus">Enabled</span></span>
                <span id="tokenExpiry">Token expires: --</span>
            </div>
            <div id="lastRefresh" style="font-size: 12px; color: #666; margin-top: 5px;">
                Last refresh: Never
            </div>
        </div>
        
        <!-- Recording Controls -->
        <div class="controls">
            <button id="startBtn" disabled>
                <span>▶️</span> Start Recording
            </button>
            <button id="stopBtn" disabled>
                <span>⏹️</span> Stop Recording
            </button>
        </div>
        
        <div id="status" class="status idle">
            Please login to start recording
        </div>
        
        <div class="transcription-box" id="transcriptionBox">
            <p style="color: #9ca3af; text-align: center;">Your transcription will appear here...</p>
        </div>
        
        <div id="finalTranscription" class="final-transcription" style="display: none;">
            <div class="final-label">✅ Final Transcription</div>
            <div class="final-text" id="finalText"></div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="chunksProcessed">0</div>
                <div class="stat-label">Chunks Processed</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="chunksSent">0</div>
                <div class="stat-label">Chunks Sent</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="duration">0s</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>
        
        <div id="errorMessage" class="error-message"></div>
        
        <details style="margin-top: 20px;">
            <summary style="cursor: pointer; color: #667eea; font-weight: 600;">🛠 Debug Log</summary>
            <div id="debugLog" class="debug-log"></div>
        </details>
    </div>

    <script>
        // ============================================================
        // CONFIGURATION
        // ============================================================
        const API_BASE_URL = 'https://ei452m2xjncwby-8000.proxy.runpod.net';
        const LOGIN_URL = `${API_BASE_URL}/login`;
        const WS_URL = 'wss://ei452m2xjncwby-8000.proxy.runpod.net/stream-transcription-auth';
        const LANGUAGE = 'en';
        const SAMPLE_RATE = 16000;
        const CHUNK_DURATION_MS = 500;
        
        // ============================================================
        // STATE
        // ============================================================
        let currentUser = null;
        let idToken = null;
        let refreshToken = null;
        let audioContext = null;
        let mediaStream = null;
        let websocket = null;
        let isRecording = false;
        let chunksProcessed = 0;
        let chunksSent = 0;
        let recordingStartTime = null;
        let audioBuffer = [];
        let tokenExpiryTime = null;
        let durationInterval = null;
        
        // ============================================================
        // DOM ELEMENTS
        // ============================================================
        const authSection = document.getElementById('authSection');
        const authStatus = document.getElementById('authStatus');
        const userInfo = document.getElementById('userInfo');
        const loginForm = document.getElementById('loginForm');
        const emailInput = document.getElementById('emailInput');
        const passwordInput = document.getElementById('passwordInput');
        const loginBtn = document.getElementById('loginBtn');
        const loginBtnText = document.getElementById('loginBtnText');
        const logoutBtn = document.getElementById('logoutBtn');
        const tokenInfo = document.getElementById('tokenInfo');
        const refreshStatus = document.getElementById('refreshStatus');
        const tokenExpiry = document.getElementById('tokenExpiry');
        const lastRefresh = document.getElementById('lastRefresh');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const status = document.getElementById('status');
        const transcriptionBox = document.getElementById('transcriptionBox');
        const finalTranscription = document.getElementById('finalTranscription');
        const finalText = document.getElementById('finalText');
        const errorMessage = document.getElementById('errorMessage');
        const debugLog = document.getElementById('debugLog');
        
        // ============================================================
        // UTILITY FUNCTIONS
        // ============================================================
        function log(message) {
            console.log(message);
            const timestamp = new Date().toLocaleTimeString();
            debugLog.innerHTML += `[${timestamp}] ${message}<br>`;
            debugLog.scrollTop = debugLog.scrollHeight;
        }
        
        function updateStatus(message, className) {
            status.textContent = message;
            status.className = `status ${className}`;
        }
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
            log('ERROR: ' + message);
            setTimeout(() => {
                errorMessage.style.display = 'none';
            }, 5000);
        }
        
        // ============================================================
        // AUTHENTICATION
        // ============================================================
        
        // Check for stored tokens on page load
        window.addEventListener('load', () => {
            const storedIdToken = localStorage.getItem('idToken');
            const storedRefreshToken = localStorage.getItem('refreshToken');
            const storedUser = localStorage.getItem('userInfo');
            
            if (storedIdToken && storedRefreshToken && storedUser) {
                idToken = storedIdToken;
                refreshToken = storedRefreshToken;
                currentUser = JSON.parse(storedUser);
                onUserAuthenticated();
                log('✅ Restored session from localStorage');
            }
        });
        
        function onUserAuthenticated() {
            log('✅ User authenticated: ' + currentUser.email);
            
            authSection.className = 'auth-section authenticated';
            authStatus.textContent = '✅ Authenticated';
            userInfo.innerHTML = `
                <div><strong>${currentUser.displayName || 'User'}</strong></div>
                <div>${currentUser.email}</div>
            `;
            userInfo.style.display = 'block';
            loginForm.style.display = 'none';
            logoutBtn.style.display = 'block';
            
            startBtn.disabled = false;
            updateStatus('Ready to start recording', 'idle');
            
            // Show token info
            tokenInfo.classList.remove('hidden');
            lastRefresh.textContent = 'Last refresh: Just logged in';
            
            // Calculate token expiry
            if (currentUser.expiresIn) {
                const expiryDate = new Date(currentUser.expiresIn);
                tokenExpiry.textContent = `Token expires: ${expiryDate.toLocaleTimeString()}`;
            }
        }
        
        function onUserLoggedOut() {
            log('🔓 User logged out');
            
            // Clear stored data
            localStorage.removeItem('idToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userInfo');
            
            currentUser = null;
            idToken = null;
            refreshToken = null;
            
            authSection.className = 'auth-section';
            authStatus.textContent = '🔒 Not Authenticated';
            userInfo.style.display = 'none';
            loginForm.style.display = 'flex';
            logoutBtn.style.display = 'none';
            
            startBtn.disabled = true;
            stopBtn.disabled = true;
            updateStatus('Please login to start recording', 'idle');
            
            tokenInfo.classList.add('hidden');
            
            // Stop recording if active
            if (isRecording) {
                stopRecording();
            }
        }
        
        // Login handler
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = emailInput.value;
            const password = passwordInput.value;
            
            try {
                log('🔐 Attempting login...');
                loginBtn.disabled = true;
                loginBtnText.innerHTML = '<div class="spinner"></div> Logging in...';
                
                const response = await fetch(LOGIN_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Login failed');
                }
                
                const data = await response.json();
                log('✅ Login successful');
                log('Response: ' + JSON.stringify(data).substring(0, 100) + '...');
                
                // Extract tokens from response
                // Based on your API response structure:
                // { "access_token": { "idToken": "...", "refreshToken": "...", ... } }
                const accessToken = data.access_token;
                
                idToken = accessToken.idToken;
                refreshToken = accessToken.refreshToken;
                
                currentUser = {
                    email: accessToken.email,
                    displayName: accessToken.displayName,
                    localId: accessToken.localId,
                    expiresIn: accessToken.expiresIn
                };
                
                // Store in localStorage
                localStorage.setItem('idToken', idToken);
                localStorage.setItem('refreshToken', refreshToken);
                localStorage.setItem('userInfo', JSON.stringify(currentUser));
                
                passwordInput.value = '';
                onUserAuthenticated();
                
            } catch (error) {
                log('❌ Login failed: ' + error.message);
                showError('Login failed: ' + error.message);
            } finally {
                loginBtn.disabled = false;
                loginBtnText.textContent = '🔑 Login';
            }
        });
        
        // Logout handler
        logoutBtn.addEventListener('click', () => {
            onUserLoggedOut();
        });
        
        // ============================================================
        // TOKEN MANAGEMENT
        // ============================================================
        function getTokens() {
            if (!idToken || !refreshToken) {
                throw new Error('No tokens available. Please login.');
            }
            return { idToken, refreshToken };
        }
        
        function updateTokenExpiry(expiresIn) {
            tokenExpiryTime = new Date(Date.now() + expiresIn * 1000);
            tokenExpiry.textContent = `Token expires: ${tokenExpiryTime.toLocaleTimeString()}`;
        }
        
        function handleTokenRefresh(data) {
            log('🔄 Token automatically refreshed by server!');
            
            // Update stored tokens
            idToken = data.id_token;
            refreshToken = data.refresh_token;
            
            localStorage.setItem('idToken', idToken);
            localStorage.setItem('refreshToken', refreshToken);
            
            // Update UI
            refreshStatus.textContent = 'Active';
            refreshStatus.style.color = '#10b981';
            lastRefresh.textContent = `Last refresh: ${new Date().toLocaleTimeString()}`;
            
            if (data.expires_in) {
                updateTokenExpiry(data.expires_in);
            }
        }
        
        // ============================================================
        // RECORDING FUNCTIONS
        // ============================================================
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        
        async function startRecording() {
            try {
                if (!idToken || !refreshToken) {
                    showError('Please login first');
                    return;
                }
                
                log('🎤 Requesting microphone access...');
                
                // Get tokens
                const tokens = getTokens();
                log('🔑 Using authentication tokens');
                
                // Request microphone
                mediaStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        channelCount: 1,
                        sampleRate: SAMPLE_RATE,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
                
                log('✅ Microphone access granted');
                
                // Create audio context
                audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: SAMPLE_RATE
                });
                
                log(`🎵 Audio context created (${audioContext.sampleRate}Hz)`);
                
                // Connect to WebSocket
                websocket = new WebSocket(WS_URL);
                
                websocket.onopen = () => {
                    log('✅ WebSocket connected');
                    
                    // Send config with authentication tokens
                    websocket.send(JSON.stringify({
                        type: 'config',
                        language: LANGUAGE,
                        id_token: tokens.idToken,
                        refresh_token: tokens.refreshToken  // Enable auto-refresh!
                    }));
                    
                    log('📤 Sent config with auth tokens (auto-refresh enabled)');
                };
                
                websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                websocket.onerror = (error) => {
                    log('❌ WebSocket error: ' + error);
                    showError('WebSocket connection error. Make sure the server is running.');
                    stopRecording();
                };
                
                websocket.onclose = () => {
                    log('🔌 WebSocket disconnected');
                };
                
                // Wait for WebSocket ready
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject(new Error('WebSocket timeout')), 5000);
                    const originalOnOpen = websocket.onopen;
                    websocket.onopen = (e) => {
                        originalOnOpen(e);
                        clearTimeout(timeout);
                        setTimeout(resolve, 100);
                    };
                    websocket.onerror = () => {
                        clearTimeout(timeout);
                        reject(new Error('WebSocket connection failed'));
                    };
                });
                
                // Create audio processor
                const source = audioContext.createMediaStreamSource(mediaStream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                processor.onaudioprocess = (e) => {
                    if (!isRecording) return;
                    
                    const inputData = e.inputBuffer.getChannelData(0);
                    audioBuffer.push(...inputData);
                    
                    const samplesNeeded = (CHUNK_DURATION_MS / 1000) * SAMPLE_RATE;
                    
                    if (audioBuffer.length >= samplesNeeded) {
                        const chunk = audioBuffer.splice(0, samplesNeeded);
                        sendAudioChunk(chunk);
                    }
                };
                
                source.connect(processor);
                processor.connect(audioContext.destination);
                
                isRecording = true;
                recordingStartTime = Date.now();
                startBtn.disabled = true;
                stopBtn.disabled = false;
                
                updateStatus('🔴 Recording... Speak now!', 'recording');
                transcriptionBox.innerHTML = '';
                finalTranscription.style.display = 'none';
                chunksProcessed = 0;
                chunksSent = 0;
                audioBuffer = [];
                
                log('🎙️ Recording started');
                
                // Update duration
                durationInterval = setInterval(() => {
                    if (isRecording) {
                        const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                        document.getElementById('duration').textContent = duration + 's';
                    }
                }, 1000);
                
            } catch (error) {
                log('❌ Error starting recording: ' + error.message);
                showError('Could not start recording: ' + error.message);
            }
        }
        
        function sendAudioChunk(audioData) {
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                log('⚠️ WebSocket not ready, skipping chunk');
                return;
            }
            
            try {
                // Convert Float32Array to Int16 PCM
                const pcmData = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    const s = Math.max(-1, Math.min(1, audioData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                
                // Create WAV file
                const wavBuffer = createWavFile(pcmData, SAMPLE_RATE);
                
                // Convert to base64
                const base64 = arrayBufferToBase64(wavBuffer);
                
                // Send to server
                websocket.send(JSON.stringify({
                    type: 'audio',
                    data: base64
                }));
                
                chunksSent++;
                document.getElementById('chunksSent').textContent = chunksSent;
                
                log(`📤 Sent chunk #${chunksSent} (${pcmData.length} samples, ${wavBuffer.byteLength} bytes)`);
                
            } catch (error) {
                log('❌ Error sending chunk: ' + error.message);
            }
        }
        
        function createWavFile(pcmData, sampleRate) {
            const numChannels = 1;
            const bytesPerSample = 2;
            const blockAlign = numChannels * bytesPerSample;
            const byteRate = sampleRate * blockAlign;
            const dataSize = pcmData.length * bytesPerSample;
            const buffer = new ArrayBuffer(44 + dataSize);
            const view = new DataView(buffer);
            
            writeString(view, 0, 'RIFF');
            view.setUint32(4, 36 + dataSize, true);
            writeString(view, 8, 'WAVE');
            writeString(view, 12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true);
            view.setUint16(22, numChannels, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, byteRate, true);
            view.setUint16(32, blockAlign, true);
            view.setUint16(34, 16, true);
            writeString(view, 36, 'data');
            view.setUint32(40, dataSize, true);
            
            let offset = 44;
            for (let i = 0; i < pcmData.length; i++) {
                view.setInt16(offset, pcmData[i], true);
                offset += 2;
            }
            
            return buffer;
        }
        
        function writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }
        
        function arrayBufferToBase64(buffer) {
            const bytes = new Uint8Array(buffer);
            let binary = '';
            for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            return btoa(binary);
        }
        
        function stopRecording() {
            log('🛑 Stopping recording...');
            
            if (durationInterval) {
                clearInterval(durationInterval);
            }
            
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
            }
            
            if (audioContext) {
                audioContext.close();
            }
            
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: 'end' }));
                log('📤 Sent end signal');
            }
            
            isRecording = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            updateStatus('⏸️ Processing final transcription...', 'processing');
        }
        
        // ============================================================
        // WEBSOCKET MESSAGE HANDLER
        // ============================================================
        function handleWebSocketMessage(data) {
            log(`📨 Received: ${data.type}` + (data.text ? ` - "${data.text.substring(0, 50)}..."` : ''));
            
            switch (data.type) {
                case 'ready':
                    log('🟢 Session ready');
                    if (data.auto_refresh_enabled) {
                        log('🔄 Auto-refresh is ENABLED - tokens will refresh every 55 minutes');
                        refreshStatus.textContent = 'Enabled';
                        refreshStatus.style.color = '#10b981';
                    } else {
                        log('⚠️ Auto-refresh is NOT enabled - session will expire in 1 hour');
                        refreshStatus.textContent = 'Disabled';
                        refreshStatus.style.color = '#ef4444';
                    }
                    break;
                    
                case 'token_refreshed':
                    handleTokenRefresh(data);
                    break;
                    
                case 'token_refresh_failed':
                    log('❌ Token refresh failed: ' + data.message);
                    showError('Session expired. Please log in again.');
                    refreshStatus.textContent = 'Failed';
                    refreshStatus.style.color = '#ef4444';
                    // Auto logout after refresh failure
                    setTimeout(() => {
                        stopRecording();
                        onUserLoggedOut();
                    }, 2000);
                    break;
                    
                case 'chunk_result':
                    chunksProcessed++;
                    document.getElementById('chunksProcessed').textContent = chunksProcessed;
                    
                    const chunkDiv = document.createElement('div');
                    chunkDiv.className = 'transcription-item';
                    chunkDiv.innerHTML = `
                        <div class="chunk-label">Chunk ${data.chunk_id} (${data.start_time.toFixed(1)}s - ${data.end_time.toFixed(1)}s)</div>
                        <div class="chunk-text">${data.text}</div>
                    `;
                    transcriptionBox.appendChild(chunkDiv);
                    transcriptionBox.scrollTop = transcriptionBox.scrollHeight;
                    break;
                    
                case 'partial':
                    log(`⚡ Partial update: "${data.text.substring(0, 50)}..."`);
                    break;
                    
                case 'complete':
                    finalTranscription.style.display = 'block';
                    finalText.textContent = data.text;
                    updateStatus('✅ Transcription complete!', 'idle');
                    log(`✅ Complete: ${data.total_chunks} chunks processed in ${data.duration}s`);
                    break;
                    
                case 'no_speech':
                    log(`🔇 No speech in chunk ${data.chunk_id}`);
                    break;
                    
                case 'error':
                    showError(data.message);
                    if (data.message.includes('Authentication') || 
                        data.message.includes('Token') ||
                        data.message.includes('authenticated')) {
                        stopRecording();
                        setTimeout(() => onUserLoggedOut(), 1000);
                    }
                    break;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    print("=" * 80)
    print("🎤 Real-Time Voice Transcription App (Authenticated with Auto-Refresh)")
    print("=" * 80)
    print("✨ Features:")
    print("   • Backend authentication via /login API")
    print("   • Automatic token refresh every 55 minutes")
    print("   • Unlimited recording sessions")
    print("   • Real-time transcription")
    print("=" * 80)
    print("📋 API Configuration:")
    print(f"   • Login API: http://127.0.0.1:8000/login")
    print(f"   • WebSocket: ws://127.0.0.1:8000/stream-transcription-auth")
    print("=" * 80)
    print("🚀 How to use:")
    print("   1. Make sure FastAPI server is running on port 8000")
    print("   2. Open browser: http://localhost:8000")
    print("   3. Login with your credentials")
    print("   4. Start recording - tokens auto-refresh every 55 minutes!")
    print("=" * 80)
    print("🌐 Starting Flask server...")
    print("   Open your browser: http://localhost:8000")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=8000)
