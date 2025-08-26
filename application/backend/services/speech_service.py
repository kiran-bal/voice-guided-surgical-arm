"""
Speech Recognition Service
Supports Web Speech API for speech-to-text conversion.
"""

import logging
from typing import Dict, Any

from ..config import Config

logger = logging.getLogger(__name__)

class SpeechRecognitionService:
    """
    Speech Recognition Service using Web Speech API.
    All transcription is handled on the frontend.
    """
    
    def __init__(self):
        self.provider = Config.SPEECH_RECOGNITION_PROVIDER
        
        logger.info(f"🎤 Speech Recognition Service initialized with provider: {self.provider}")
    
    def transcribe_audio(self, audio_data: str, audio_format: str = 'wav') -> Dict[str, Any]:
        """
        Transcribe audio using Web Speech API (frontend-handled).
        
        Args:
            audio_data: Base64 encoded audio data (not used for Web Speech API)
            audio_format: Audio format (not used for Web Speech API)
            
        Returns:
            Dictionary with transcription result
        """
        return {
            "success": True,
            "transcription": "",
            "confidence": 0.0,
            "provider": "web_speech",
            "message": "Web Speech API transcription handled on frontend"
        }
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get speech recognition configuration.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "provider": self.provider,
            "available_providers": ["web_speech"]
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test speech recognition service connection.
        
        Returns:
            Dictionary with test results
        """
        return {
            "success": True,
            "provider": "web_speech",
            "message": "Web Speech API available (browser-based)"
        }
