/**
 * ASTRA Surgical Assistant Voice Control Application
 * Handles voice recording, transcription, and API communication
 */

class ASTRAApp {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isRecording = false;
        this.transcription = '';
        this.recordingTimeout = null;
        this.currentResults = null;
        this.automaticMode = false;
        this.automaticListenDuration = 3;
        this.automaticTimer = null;
        this.automaticModeEnabled = false;
        this.speechProvider = 'web_speech';
        
        this.initializeElements();
        this.initializeSpeechRecognition();
        this.bindEvents();
        this.loadSystemStatus();
    }

    initializeElements() {
        // Voice recording elements
        this.micButton = document.getElementById('micButton');
        this.recordingAnimation = document.getElementById('recordingAnimation');
        this.transcriptionContainer = document.getElementById('transcriptionContainer');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.actionButtons = document.getElementById('actionButtons');
        
        // Action buttons
        this.stopButton = document.getElementById('stopButton');
        this.discardButton = document.getElementById('discardButton');
        this.sendButton = document.getElementById('sendButton');
        
        // Modal elements
        this.resultsModal = document.getElementById('resultsModal');
        this.modalResultsContent = document.getElementById('modalResultsContent');
        this.closeModal = document.getElementById('closeModal');
        this.clearResults = document.getElementById('clearResults');
        
        // Status elements
        this.llmStatus = document.getElementById('llmStatus');
        this.cameraStatus = document.getElementById('cameraStatus');
        this.esp32Status = document.getElementById('esp32Status');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        // Automatic mode elements
        this.automaticModeIndicator = document.getElementById('automaticModeIndicator');
        this.autoModeTimer = document.getElementById('autoModeTimer');
        
        // Results button
        this.resultsButton = document.getElementById('resultsButton');
        this.viewResultsButton = document.getElementById('viewResultsButton');
    }

    initializeSpeechRecognition() {
        // Check if Web Speech API is supported
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
            return;
        }

        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition settings
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;

        // Bind recognition events
        this.recognition.onstart = () => {
            console.log('🎤 Speech recognition started');
            this.isRecording = true;
            this.updateUIForRecording();
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            this.transcription = finalTranscript;
            this.transcriptionText.textContent = finalTranscript + interimTranscript;
            
            // Auto-stop after 10 seconds of silence
            this.resetRecordingTimeout();
        };

        this.recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            this.stopRecording();
            
            if (event.error === 'no-speech') {
                this.showMessage('No speech detected. Please try again.');
            } else if (event.error === 'audio-capture') {
                this.showError('Microphone access denied. Please allow microphone access.');
            } else {
                this.showError(`Speech recognition error: ${event.error}`);
            }
        };

        this.recognition.onend = () => {
            console.log('🎤 Speech recognition ended');
            this.isRecording = false;
            this.updateUIForStopped();
        };
    }

    bindEvents() {
        // Microphone button
        this.micButton.addEventListener('click', () => {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startAutomaticMode();
            }
        });

        // Action buttons
        this.stopButton.addEventListener('click', () => this.stopRecording());
        this.discardButton.addEventListener('click', () => this.discardRecording());
        this.sendButton.addEventListener('click', () => this.sendInstruction());

        // Modal buttons
        this.closeModal.addEventListener('click', () => this.hideResultsModal());
        this.clearResults.addEventListener('click', () => this.clearResults());
        
        // Results button
        this.viewResultsButton.addEventListener('click', () => this.showResultsModal());
        
        // Close modal when clicking outside
        this.resultsModal.addEventListener('click', (e) => {
            if (e.target === this.resultsModal) {
                this.hideResultsModal();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !this.isRecording) {
                e.preventDefault();
                this.startRecording();
            } else if (e.code === 'Escape' && this.isRecording) {
                this.stopRecording();
            } else if (e.code === 'Escape' && !this.resultsModal.classList.contains('hidden')) {
                this.hideResultsModal();
            }
        });
    }

    startRecording() {
        this.startWebSpeechRecording();
    }

    startWebSpeechRecording() {
        if (!this.recognition) {
            this.showError('Speech recognition not available');
            return;
        }

        try {
            this.transcription = '';
            this.transcriptionText.textContent = 'Start speaking...';
            this.recognition.start();
            
            // If in automatic mode, start the timer
            if (this.automaticModeEnabled) {
                this.startAutomaticTimer();
            }
        } catch (error) {
            console.error('❌ Error starting Web Speech recording:', error);
            this.showError('Failed to start recording. Please try again.');
        }
    }





    stopRecording() {
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
        this.clearRecordingTimeout();
        
        // In manual mode, keep the action buttons visible after stopping
        if (!this.automaticModeEnabled && this.transcription.trim()) {
            // Don't hide action buttons - let user choose to send or discard
        }
    }



    discardRecording() {
        this.stopRecording();
        this.transcription = '';
        this.transcriptionText.textContent = 'Start speaking...';
        this.hideActionButtons();
        this.hideTranscription();
    }

    async sendInstruction() {
        if (!this.transcription.trim()) {
            this.showError('No transcription to send');
            return;
        }

        this.showLoading(true);
        
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    instruction: this.transcription
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.currentResults = result;
                this.showResultsButton();
                this.showMessage('✅ Instruction processed successfully!');
            } else {
                this.showError(`❌ Error: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('❌ API request error:', error);
            this.showError('❌ Failed to send instruction. Please check your connection.');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(result) {
        // Store results for modal display
        this.currentResults = result;
        
        // Show results in modal (only in manual mode)
        if (!this.automaticModeEnabled) {
            this.showResultsModal();
        } else {
            this.showResultsButton();
        }
    }

    showResultsModal() {
        if (this.currentResults) {
            this.modalResultsContent.innerHTML = `<pre>${JSON.stringify(this.currentResults, null, 2)}</pre>`;
            this.resultsModal.classList.remove('hidden');
            
            // Trigger animation
            setTimeout(() => {
                this.resultsModal.classList.add('show');
            }, 10);
        }
    }

    hideResultsModal() {
        this.resultsModal.classList.remove('show');
        setTimeout(() => {
            this.resultsModal.classList.add('hidden');
        }, 300);
    }

    clearResults() {
        this.currentResults = null;
        this.hideResultsModal();
        this.hideResultsButton();
    }

    updateUIForRecording() {
        this.micButton.classList.add('recording');
        this.recordingAnimation.classList.remove('hidden');
        this.showTranscription();
        
        // Show automatic mode indicator if enabled
        if (this.automaticModeEnabled) {
            this.showAutomaticModeIndicator();
        } else {
            // Show action buttons in manual mode for both providers
            this.showActionButtons();
        }
    }

    updateUIForStopped() {
        this.micButton.classList.remove('recording');
        this.recordingAnimation.classList.add('hidden');
        this.hideAutomaticModeIndicator();
        this.stopAutomaticTimer();
        
        // Only hide action buttons if in automatic mode
        if (this.automaticModeEnabled) {
            this.hideActionButtons();
        }
    }

    showTranscription() {
        this.transcriptionContainer.classList.remove('hidden');
    }

    hideTranscription() {
        this.transcriptionContainer.classList.add('hidden');
    }

    showActionButtons() {
        this.actionButtons.classList.remove('hidden');
    }

    hideActionButtons() {
        this.actionButtons.classList.add('hidden');
    }

    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.remove('hidden');
        } else {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    resetRecordingTimeout() {
        this.clearRecordingTimeout();
        this.recordingTimeout = setTimeout(() => {
            if (this.isRecording) {
                this.stopRecording();
            }
        }, 10000); // 10 seconds
    }

    clearRecordingTimeout() {
        if (this.recordingTimeout) {
            clearTimeout(this.recordingTimeout);
            this.recordingTimeout = null;
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            if (response.ok) {
                // Update speech recognition provider
                this.speechProvider = status.config.speech_recognition_provider || 'web_speech';
                console.log(`🎤 Speech recognition provider: ${this.speechProvider}`);
                
                this.updateStatusDisplay(status);
                this.updateAutomaticModeConfig(status);
            }
        } catch (error) {
            console.error('❌ Error loading system status:', error);
            this.updateStatusDisplay({
                config: { llm_provider: 'Unknown', use_camera: false, use_esp32: false },
                services: { llm: 'Error', camera: 'Error', esp32: 'Error' }
            });
        }
    }

    updateStatusDisplay(status) {
        const config = status.config || {};
        const services = status.services || {};
        
        // Update LLM status
        this.llmStatus.textContent = config.llm_provider || 'Unknown';
        this.llmStatus.style.color = services.llm === 'initialized' ? '#4cc9f0' : '#ef4444';
        
        // Update camera status
        const cameraText = config.use_camera ? 'Enabled' : 'Disabled (Test Mode)';
        this.cameraStatus.textContent = cameraText;
        this.cameraStatus.style.color = config.use_camera ? '#4cc9f0' : '#f59e0b';
        
        // Update ESP32 status
        const esp32Text = config.use_esp32 ? 'Connected' : 'Disabled (Test Mode)';
        this.esp32Status.textContent = esp32Text;
        this.esp32Status.style.color = config.use_esp32 ? '#4cc9f0' : '#f59e0b';
    }

    showMessage(message) {
        // Create a temporary message element
        const messageEl = document.createElement('div');
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
            z-index: 1001;
            font-weight: 500;
            max-width: 300px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(16, 185, 129, 0.2);
        `;
        messageEl.textContent = message;
        
        document.body.appendChild(messageEl);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 3000);
    }

    showError(message) {
        // Create a temporary error element
        const errorEl = document.createElement('div');
        errorEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);
            z-index: 1001;
            font-weight: 500;
            max-width: 300px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(239, 68, 68, 0.2);
        `;
        errorEl.textContent = message;
        
        document.body.appendChild(errorEl);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (errorEl.parentNode) {
                errorEl.parentNode.removeChild(errorEl);
            }
        }, 5000);
    }

    updateAutomaticModeConfig(status) {
        const config = status.config || {};
        this.automaticModeEnabled = config.automatic_mode || false;
        this.automaticListenDuration = config.automatic_listen_duration || 3;
        this.speechProvider = config.speech_recognition_provider || 'web_speech';
        
        console.log(`🤖 Automatic mode: ${this.automaticModeEnabled ? 'enabled' : 'disabled'}`);
        console.log(`⏱️ Listen duration: ${this.automaticListenDuration}s`);
        console.log(`🎤 Speech provider: ${this.speechProvider}`);
    }

    startAutomaticMode() {
        if (!this.automaticModeEnabled) {
            this.startRecording();
            return;
        }

        console.log('🤖 Starting automatic mode');
        this.startRecording();
        this.showAutomaticModeIndicator();
    }

    showAutomaticModeIndicator() {
        this.automaticModeIndicator.classList.remove('hidden');
        this.autoModeTimer.textContent = this.automaticListenDuration;
    }

    hideAutomaticModeIndicator() {
        this.automaticModeIndicator.classList.add('hidden');
    }

    startAutomaticTimer() {
        // Clear any existing timer
        this.stopAutomaticTimer();
        
        let timeLeft = this.automaticListenDuration;
        this.autoModeTimer.textContent = timeLeft;
        
        console.log(`⏱️ Starting automatic timer for ${timeLeft} seconds`);
        
        this.automaticTimer = setInterval(() => {
            timeLeft--;
            this.autoModeTimer.textContent = timeLeft;
            
            console.log(`⏱️ Automatic timer: ${timeLeft} seconds remaining`);
            
            if (timeLeft <= 0) {
                console.log('⏱️ Automatic timer expired, processing instruction');
                this.stopAutomaticTimer();
                this.stopRecording();
                this.hideAutomaticModeIndicator();
                
                // For Web Speech API, process immediately
                if (this.transcription.trim()) {
                    this.sendInstructionAutomatic();
                } else {
                    this.showError('No speech detected during automatic recording');
                }
            }
        }, 1000);
    }

    stopAutomaticTimer() {
        if (this.automaticTimer) {
            clearInterval(this.automaticTimer);
            this.automaticTimer = null;
        }
    }

    async sendInstructionAutomatic() {
        if (!this.transcription.trim()) {
            return;
        }

        this.showLoading(true);
        
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    instruction: this.transcription
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.currentResults = result;
                this.showResultsButton();
                this.showMessage('✅ Instruction processed successfully!');
            } else {
                this.showError(`❌ Error: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('❌ API request error:', error);
            this.showError('❌ Failed to send instruction. Please check your connection.');
        } finally {
            this.showLoading(false);
        }
    }

    showResultsButton() {
        this.resultsButton.classList.remove('hidden');
    }

    hideResultsButton() {
        this.resultsButton.classList.add('hidden');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing ASTRA Surgical Assistant Application');
    window.astraApp = new ASTRAApp();
});
