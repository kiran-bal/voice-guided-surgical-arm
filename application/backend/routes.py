"""
API routes for the surgical assistant application.
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from .services import LLMService, CameraService, CommandService, ESP32Service, SpeechRecognitionService
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
llm_service = LLMService()
camera_service = CameraService()
command_service = CommandService()
esp32_service = ESP32Service()
speech_service = SpeechRecognitionService()


@api.route('/process', methods=['POST'])
def process_instruction() -> Dict[str, Any]:
    """
    Process a surgical instruction through the complete pipeline.
    
    Expected input:
    {
        "instruction": "string"
    }
    
    Returns:
    {
        "llm_result": {...},
        "detection": {...},
        "command": "string",
        "esp32_response": {...}
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({
                "error": "Missing 'instruction' field in request body"
            }), 400
        
        instruction = data['instruction']
        if not instruction or not isinstance(instruction, str):
            return jsonify({
                "error": "Instruction must be a non-empty string"
            }), 400
        
        logger.info(f"🔄 Processing instruction: {instruction}")
        
        # Step 1: Process instruction with LLM
        logger.info("📝 Step 1: Processing with LLM")
        llm_result = llm_service.process_instruction(instruction)
        
        # Step 2: Detect objects with camera
        logger.info("📷 Step 2: Object detection")
        detection = camera_service.detect_object()
        
        # Step 3: Map to command
        logger.info("🎯 Step 3: Mapping to command")
        command = command_service.map_to_command(llm_result, detection)
        
        # Step 4: Send command to ESP32
        logger.info("📡 Step 4: Sending to ESP32")
        esp32_response = esp32_service.send_command(command)
        
        # Prepare response
        response = {
            "llm_result": llm_result,
            "detection": detection,
            "command": command,
            "esp32_response": esp32_response,
            "success": True
        }
        
        logger.info(f"✅ Processing completed successfully")
        logger.info(f"   - Command sent: {command}")
        logger.info(f"   - ESP32 success: {esp32_response.get('success', False)}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error processing instruction: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "success": False
        }), 500


@api.route('/status', methods=['GET'])
def get_status() -> Dict[str, Any]:
    """
    Get system status and configuration.
    
    Returns:
    {
        "config": {...},
        "services": {...}
    }
    """
    try:
        status = {
            "config": {
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL,
                "use_camera": Config.USE_CAMERA,
                "use_esp32": Config.USE_ESP32,
                "esp32_address": Config.ESP32_ADDRESS,
                "debug": Config.DEBUG,
                "automatic_mode": Config.AUTOMATIC_MODE,
                "automatic_listen_duration": Config.AUTOMATIC_LISTEN_DURATION,
                "speech_recognition_provider": Config.SPEECH_RECOGNITION_PROVIDER
            },
            "services": {
                "llm": "initialized",
                "camera": camera_service.get_configuration(),
                "command": "initialized",
                "esp32": esp32_service.get_status(),
                "speech": speech_service.get_configuration()
            },
            "command_map": Config.COMMAND_MAP,
            "doctor_profiles": Config.DOCTOR_PROFILES
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@api.route('/test', methods=['GET'])
def test_services() -> Dict[str, Any]:
    """
    Test all services and return their status.
    
    Returns:
    {
        "llm_test": {...},
        "camera_test": {...},
        "esp32_test": {...}
    }
    """
    try:
        # Test LLM service
        llm_test = llm_service.process_instruction("hi sarath, you can start the incision")
        
        # Test camera service
        camera_test = camera_service.detect_object()
        
        # Test ESP32 service
        esp32_test = esp32_service.test_connection()
        
        # Test speech recognition service
        speech_test = speech_service.test_connection()
        
        test_results = {
            "llm_test": llm_test,
            "camera_test": camera_test,
            "esp32_test": esp32_test,
            "speech_test": speech_test,
            "success": True
        }
        
        return jsonify(test_results)
        
    except Exception as e:
        logger.error(f"❌ Error testing services: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "success": False
        }), 500


@api.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint.
    
    Returns:
    {
        "status": "healthy",
        "timestamp": "..."
    }
    """
    from datetime import datetime
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "surgical-assistant-api"
    })


@api.route('/prompts/config', methods=['GET'])
def get_prompt_configs() -> Dict[str, Any]:
    """
    Get available prompt configurations.
    
    Returns:
    {
        "configs": ["default", "detailed", "conservative"],
        "current": "default"
    }
    """
    try:
        configs = llm_service.get_available_prompt_configs()
        return jsonify({
            "configs": configs,
            "current": "default"  # TODO: track current config
        })
    except Exception as e:
        logger.error(f"❌ Error getting prompt configs: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@api.route('/prompts/config', methods=['POST'])
def set_prompt_config() -> Dict[str, Any]:
    """
    Set prompt configuration.
    
    Expected input:
    {
        "config": "detailed"
    }
    
    Returns:
    {
        "success": true,
        "config": "detailed"
    }
    """
    try:
        data = request.get_json()
        if not data or 'config' not in data:
            return jsonify({
                "error": "Missing 'config' field in request body"
            }), 400
        
        config_name = data['config']
        llm_service.set_prompt_config(config_name)
        
        return jsonify({
            "success": True,
            "config": config_name,
            "message": f"Prompt configuration changed to: {config_name}"
        })
        
    except Exception as e:
        logger.error(f"❌ Error setting prompt config: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@api.route('/commands/mappings', methods=['GET'])
def get_command_mappings() -> Dict[str, Any]:
    """
    Get all command mappings.
    
    Returns:
    {
        "mappings": {...},
        "actions": ["incision", "stitch", "grasp", "cut"]
    }
    """
    try:
        mappings = command_service.get_all_mappings()
        actions = [key for key in mappings.keys() if not key.endswith('_with_object')]
        
        return jsonify({
            "mappings": mappings,
            "actions": actions
        })
    except Exception as e:
        logger.error(f"❌ Error getting command mappings: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@api.route('/commands/mappings', methods=['POST'])
def add_command_mapping() -> Dict[str, Any]:
    """
    Add a new command mapping.
    
    Expected input:
    {
        "action": "grasp",
        "command_without_object": "d0",
        "command_with_object": "d1"
    }
    
    Returns:
    {
        "success": true,
        "action": "grasp",
        "mappings_added": 2
    }
    """
    try:
        data = request.get_json()
        if not data or 'action' not in data or 'command_without_object' not in data:
            return jsonify({
                "error": "Missing required fields: 'action' and 'command_without_object'"
            }), 400
        
        action = data['action']
        command_without_object = data['command_without_object']
        command_with_object = data.get('command_with_object')
        
        command_service.add_action_mapping(action, command_without_object, command_with_object)
        
        mappings_added = 2 if command_with_object else 1
        
        return jsonify({
            "success": True,
            "action": action,
            "mappings_added": mappings_added,
            "message": f"Added {mappings_added} mapping(s) for action: {action}"
        })
        
    except Exception as e:
        logger.error(f"❌ Error adding command mapping: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500



