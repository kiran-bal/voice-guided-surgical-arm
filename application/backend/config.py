"""
Configuration module for the Flask application.
Loads environment variables and provides configuration settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Server settings
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', 5000))
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Hardware settings
    USE_CAMERA: bool = os.getenv('USE_CAMERA', 'False').lower() == 'true'
    USE_ESP32: bool = os.getenv('USE_ESP32', 'False').lower() == 'true'
    
    # LLM settings
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'openai')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    
    # ESP32 settings
    ESP32_ADDRESS: str = os.getenv('ESP32_ADDRESS', 'http://192.168.0.131')
    
    # Camera detection settings
    CAMERA_DETECTION_DISTANCE: float = float(os.getenv('CAMERA_DETECTION_DISTANCE', '30.0'))  # cm
    CAMERA_DETECTION_HEIGHT: float = float(os.getenv('CAMERA_DETECTION_HEIGHT', '15.0'))  # cm
    CAMERA_HEIGHT_TOLERANCE: float = float(os.getenv('CAMERA_HEIGHT_TOLERANCE', '5.0'))  # cm
    CAMERA_DISTANCE_TOLERANCE: float = float(os.getenv('CAMERA_DISTANCE_TOLERANCE', '10.0'))  # cm
    CAMERA_PIXELS_PER_CM: float = float(os.getenv('CAMERA_PIXELS_PER_CM', '10.0'))  # pixels per cm calibration
    
    # Camera color detection settings
    CAMERA_DETECT_COLOR: str = os.getenv('CAMERA_DETECT_COLOR', 'green').lower()
    CAMERA_COLOR_LOWER_HSV: str = os.getenv('CAMERA_COLOR_LOWER_HSV', '35,40,40')  # H,S,V values
    CAMERA_COLOR_UPPER_HSV: str = os.getenv('CAMERA_COLOR_UPPER_HSV', '90,255,255')  # H,S,V values
    
    # Camera detection mode
    CAMERA_DETECTION_MODE: str = os.getenv('CAMERA_DETECTION_MODE', 'full').lower()  # 'full' or 'color_only'
    CAMERA_COLOR_ONLY_MIN_AREA: int = int(os.getenv('CAMERA_COLOR_ONLY_MIN_AREA', '500'))  # minimum contour area for color-only mode
    
    # Automatic mode settings
    AUTOMATIC_MODE: bool = os.getenv('AUTOMATIC_MODE', 'false').lower() == 'true'
    AUTOMATIC_LISTEN_DURATION: int = int(os.getenv('AUTOMATIC_LISTEN_DURATION', '3'))  # seconds
    
    # Speech recognition settings
    SPEECH_RECOGNITION_PROVIDER: str = os.getenv('SPEECH_RECOGNITION_PROVIDER', 'web_speech').lower()  # 'web_speech' only
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    OPENROUTER_API_KEY: Optional[str] = os.getenv('OPENROUTER_API_KEY')
    
    # Doctor profiles (from reference code)
    DOCTOR_PROFILES = {
        "sharath": {"handedness": "right"},
        "sarath": {"handedness": "right"},
        "sarad": {"handedness": "right"},
        "sharad": {"handedness": "right"},
        "kiran": {"handedness": "left"}
    }
    
    # Enhanced command mapping with action + object detection combinations
    # Note: Commands are automatically suffixed with handedness ('l' for left, 'r' for right)
    # Final commands: a0l, a0r, a1l, a1r, b0l, b0r, b1l, b1r, d0l, d0r, d1l, d1r, e0l, e0r, e1l, e1r, x
    COMMAND_MAP = {
        # Basic actions (no object detection)
        "incision": "a0",
        "stitch": "b0",
        
        # Actions with object detection
        "incision_with_object": "a1",
        "stitch_with_object": "b1",
        
        # Additional actions (extensible)
        "grasp": "d0",
        "grasp_with_object": "d1",
        "cut": "e0", 
        "cut_with_object": "e1"
    }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings."""
        if cls.LLM_PROVIDER not in ['openai', 'ollama', 'openrouter']:
            raise ValueError(f"Invalid LLM_PROVIDER: {cls.LLM_PROVIDER}")
        
        if cls.LLM_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            print("⚠️ Warning: OPENAI_API_KEY not set for OpenAI provider")
        
        if cls.LLM_PROVIDER == 'openrouter' and not cls.OPENROUTER_API_KEY:
            print("⚠️ Warning: OPENROUTER_API_KEY not set for OpenRouter provider")
        
        print(f"✅ Configuration loaded:")
        print(f"   - LLM Provider: {cls.LLM_PROVIDER}")
        print(f"   - LLM Model: {cls.LLM_MODEL}")
        print(f"   - Use Camera: {cls.USE_CAMERA}")
        print(f"   - Use ESP32: {cls.USE_ESP32}")
        print(f"   - ESP32 Address: {cls.ESP32_ADDRESS}")
        print(f"   - Camera Detection Distance: {cls.CAMERA_DETECTION_DISTANCE} cm")
        print(f"   - Camera Detection Height: {cls.CAMERA_DETECTION_HEIGHT} cm")
        print(f"   - Camera Height Tolerance: {cls.CAMERA_HEIGHT_TOLERANCE} cm")
        print(f"   - Camera Distance Tolerance: {cls.CAMERA_DISTANCE_TOLERANCE} cm")
        print(f"   - Camera Pixels per CM: {cls.CAMERA_PIXELS_PER_CM}")
        print(f"   - Camera Detect Color: {cls.CAMERA_DETECT_COLOR}")
        print(f"   - Camera Color HSV Range: {cls.CAMERA_COLOR_LOWER_HSV} - {cls.CAMERA_COLOR_UPPER_HSV}")
        print(f"   - Camera Detection Mode: {cls.CAMERA_DETECTION_MODE}")
        if cls.CAMERA_DETECTION_MODE == 'color_only':
            print(f"   - Camera Color-Only Min Area: {cls.CAMERA_COLOR_ONLY_MIN_AREA}")
        print(f"   - Automatic Mode: {cls.AUTOMATIC_MODE}")
        if cls.AUTOMATIC_MODE:
            print(f"   - Automatic Listen Duration: {cls.AUTOMATIC_LISTEN_DURATION}s")
        print(f"   - Speech Recognition Provider: {cls.SPEECH_RECOGNITION_PROVIDER}")
        print(f"   - Debug Mode: {cls.DEBUG}")
