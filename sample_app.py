"""
Improved Flask Real-Time Audio Transcription App

Uses AudioWorklet for better audio capture and WAV conversion.
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
    <title>Real-Time Voice Transcription</title>
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
            max-width: 800px;
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
        
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
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
        
        .recording-indicator {
            width: 12px;
            height: 12px;
            background: #ef4444;
            border-radius: 50%;
            display: inline-block;
            animation: blink 1s ease-in-out infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Real-Time Voice Transcription</h1>
        <p class="subtitle">Speak into your microphone and see live transcription</p>
        
        <div class="controls">
            <button id="startBtn">
                <span>▶️</span> Start Recording
            </button>
            <button id="stopBtn" disabled>
                <span>⏹️</span> Stop Recording
            </button>
        </div>
        
        <div id="status" class="status idle">
            Ready to start
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
            <summary style="cursor: pointer; color: #667eea; font-weight: 600;">🐛 Debug Log</summary>
            <div id="debugLog" class="debug-log"></div>
        </details>
    </div>

    <script>
        // Configuration
        const WS_URL = 'wss://ei452m2xjncwby-8000.proxy.runpod.net/stream-transcription';
        const LANGUAGE = 'en';
        const SAMPLE_RATE = 16000;
        const CHUNK_DURATION_MS = 500; // Send every 500ms
        
        // State
        let audioContext = null;
        let mediaStream = null;
        let audioWorkletNode = null;
        let websocket = null;
        let isRecording = false;
        let chunksProcessed = 0;
        let chunksSent = 0;
        let recordingStartTime = null;
        let audioBuffer = [];
        
        // Elements
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const status = document.getElementById('status');
        const transcriptionBox = document.getElementById('transcriptionBox');
        const finalTranscription = document.getElementById('finalTranscription');
        const finalText = document.getElementById('finalText');
        const errorMessage = document.getElementById('errorMessage');
        const debugLog = document.getElementById('debugLog');
        
        // Event listeners
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        
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
        
        async function startRecording() {
            try {
                log('🎤 Requesting microphone access...');
                
                // Request microphone access
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
                    
                    // Send config
                    websocket.send(JSON.stringify({
                        type: 'config',
                        language: LANGUAGE,
                        hospital_id: 'web_app',
                        user_id: 'web_user'
                    }));
                    
                    log('📤 Sent config message');
                };
                
                websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                websocket.onerror = (error) => {
                    log('❌ WebSocket error: ' + error);
                    showError('WebSocket connection error. Make sure the server is running on port 8000.');
                    stopRecording();
                };
                
                websocket.onclose = () => {
                    log('🔌 WebSocket disconnected');
                };
                
                // Wait for WebSocket to be ready
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject(new Error('WebSocket timeout')), 5000);
                    websocket.onopen = () => {
                        clearTimeout(timeout);
                        websocket.send(JSON.stringify({
                            type: 'config',
                            language: LANGUAGE,
                            hospital_id: 'web_app',
                            user_id: 'web_user'
                        }));
                        resolve();
                    };
                    websocket.onerror = () => {
                        clearTimeout(timeout);
                        reject(new Error('WebSocket connection failed'));
                    };
                });
                
                // Create audio source
                const source = audioContext.createMediaStreamSource(mediaStream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                processor.onaudioprocess = (e) => {
                    if (!isRecording) return;
                    
                    const inputData = e.inputBuffer.getChannelData(0);
                    audioBuffer.push(...inputData);
                    
                    // Check if we have enough data for a chunk (500ms)
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
                setInterval(() => {
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
                
                log(`📤 Sent chunk #${chunksSent} (${pcmData.length} samples, ${wavBuffer.byteLength} bytes WAV)`);
                
            } catch (error) {
                log('❌ Error sending chunk: ' + error.message);
            }
        }
        
        function createWavFile(pcmData, sampleRate) {
            const numChannels = 1;
            const bytesPerSample = 2; // 16-bit
            const blockAlign = numChannels * bytesPerSample;
            const byteRate = sampleRate * blockAlign;
            const dataSize = pcmData.length * bytesPerSample;
            const buffer = new ArrayBuffer(44 + dataSize);
            const view = new DataView(buffer);
            
            // RIFF chunk descriptor
            writeString(view, 0, 'RIFF');
            view.setUint32(4, 36 + dataSize, true);
            writeString(view, 8, 'WAVE');
            
            // fmt sub-chunk
            writeString(view, 12, 'fmt ');
            view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
            view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
            view.setUint16(22, numChannels, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, byteRate, true);
            view.setUint16(32, blockAlign, true);
            view.setUint16(34, 16, true); // BitsPerSample
            
            // data sub-chunk
            writeString(view, 36, 'data');
            view.setUint32(40, dataSize, true);
            
            // Write PCM samples
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
        
        function handleWebSocketMessage(data) {
            log(`📨 Received: ${data.type}` + (data.text ? ` - "${data.text.substring(0, 50)}..."` : ''));
            
            switch (data.type) {
                case 'ready':
                    log('🟢 Session ready');
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
                    log(`✅ Complete: ${data.total_chunks} chunks processed`);
                    break;
                    
                case 'no_speech':
                    log(`🔇 No speech in chunk ${data.chunk_id}`);
                    break;
                    
                case 'error':
                    showError(data.message);
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
    print("=" * 60)
    print("🎤 Real-Time Voice Transcription App (Improved)")
    print("=" * 60)
    print("Starting Flask server...")
    print("Open your browser and go to: http://localhost:8000")
    print("Make sure FastAPI server is running on port 8000!")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8000)
