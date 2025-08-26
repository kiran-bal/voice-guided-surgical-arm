"""
ESP32 Service for sending commands to the ESP32 device.
Sends HTTP GET requests to control the robotic arm.
"""

import logging
import requests
from typing import Dict, Any, Optional

from ..config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESP32Service:
    """Service for communicating with ESP32 device."""
    
    def __init__(self):
        """Initialize the ESP32 service."""
        self.use_esp32 = Config.USE_ESP32
        self.esp32_address = Config.ESP32_ADDRESS
        self.timeout = 5  # 5 second timeout for requests
        
        if self.use_esp32:
            logger.info(f"✅ ESP32 Service initialized with address: {self.esp32_address}")
        else:
            logger.info("✅ ESP32 Service initialized in test mode (ESP32 disabled)")
    
    def send_command(self, letter: str) -> Dict[str, Any]:
        """
        Send a command letter to the ESP32 device.
        
        Args:
            letter: Single letter command to send
            
        Returns:
            Dictionary containing response information
        """
        if not self.use_esp32:
            logger.info(f"🚫 ESP32 disabled - would send command: {letter}")
            return {
                "success": True,
                "command": letter,
                "response": "OK (test mode)",
                "mode": "test"
            }
        
        try:
            logger.info(f"📡 Sending command '{letter}' to ESP32 at {self.esp32_address}")
            
            # Prepare request parameters (based on ESP32 code structure)
            params = {"value": letter}
            
            # Send HTTP GET request
            response = requests.get(
                f"{self.esp32_address}/cmd",
                params=params,
                timeout=self.timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                logger.info(f"✅ ESP32 command sent successfully: {letter}")
                return {
                    "success": True,
                    "command": letter,
                    "response": response.text,
                    "status_code": response.status_code,
                    "url": response.url
                }
            else:
                logger.error(f"❌ ESP32 request failed with status {response.status_code}")
                return {
                    "success": False,
                    "command": letter,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ ESP32 request timeout for command: {letter}")
            return {
                "success": False,
                "command": letter,
                "error": "Request timeout",
                "timeout": True
            }
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ ESP32 connection error for command: {letter}")
            return {
                "success": False,
                "command": letter,
                "error": "Connection error - ESP32 not reachable"
            }
            
        except Exception as e:
            logger.error(f"❌ ESP32 request error: {e}")
            return {
                "success": False,
                "command": letter,
                "error": f"Request error: {str(e)}"
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to ESP32 device.
        
        Returns:
            Dictionary containing connection test results
        """
        if not self.use_esp32:
            logger.info("🚫 ESP32 disabled - skipping connection test")
            return {
                "success": True,
                "mode": "test",
                "message": "ESP32 disabled in configuration"
            }
        
        try:
            logger.info(f"🔍 Testing connection to ESP32 at {self.esp32_address}")
            
            # Try to connect to ESP32
            response = requests.get(
                self.esp32_address,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("✅ ESP32 connection test successful")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "ESP32 is reachable"
                }
            else:
                logger.warning(f"⚠️ ESP32 responded with status {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": f"ESP32 responded with status {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ ESP32 connection test timeout")
            return {
                "success": False,
                "error": "Connection timeout",
                "message": "ESP32 is not responding"
            }
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ ESP32 connection test failed")
            return {
                "success": False,
                "error": "Connection error",
                "message": "ESP32 is not reachable"
            }
            
        except Exception as e:
            logger.error(f"❌ ESP32 connection test error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Connection test failed: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get ESP32 service status.
        
        Returns:
            Dictionary containing service status
        """
        return {
            "enabled": self.use_esp32,
            "address": self.esp32_address,
            "timeout": self.timeout
        }

