"""
Command Service for mapping LLM results and camera detection to ESP32 commands.
"""

import logging
from typing import Dict, Any, Optional

from ..config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandService:
    """Service for mapping surgical actions to ESP32 commands."""
    
    def __init__(self):
        """Initialize the command service."""
        self.command_map = Config.COMMAND_MAP
        self.synonyms = dict(getattr(Config, "ACTION_SYNONYMS", {}))
        logger.info(f"✅ Command Service initialized with command map: {self.command_map}")
    
    def map_to_command(self, llm_result: Dict[str, Any], detection: Dict[str, Any]) -> str:
        """
        Map LLM result and camera detection to enhanced command.
        
        Logic:
        - If incision detected + no object: send a0
        - If incision detected + object: send a1  
        - If stitch detected + no object: send b0
        - If stitch detected + object: send b1
        - Append handedness suffix: 'l' for left, 'r' for right
        - If no action detected: send x
        
        Args:
            llm_result: Result from LLM service containing tool, action, handedness
            detection: Result from camera service containing object detection info
            
        Returns:
            Command string for ESP32 with handedness suffix or 'x' if no action
        """
        try:
            logger.info(f"🔄 Mapping to command - LLM: {llm_result}, Detection: {detection}")
            
            # Get handedness from LLM result
            handedness = llm_result.get("handedness", "right").lower()  # Default to right if not specified
            handedness_suffix = "l" if handedness == "left" else "r"
            logger.info(f"🤚 Handedness detected: {handedness} → suffix: {handedness_suffix}")
            
            # Check if object detection criteria are met
            object_detected = detection.get("object_detected", False)
            height_match = detection.get("height_match", False)
            distance_match = detection.get("distance_match", False)
            
            # Handle color-only mode
            if detection.get("color_only_detected") is not None:
                # Color-only mode: only check if color was detected
                object_criteria_met = detection.get("color_only_detected", False)
                logger.info(f"🎨 Color-only mode: {object_criteria_met}")
            else:
                # Full mode: check all criteria
                object_criteria_met = object_detected and height_match and distance_match
            
            logger.info(f"📊 Object detection status:")
            logger.info(f"   - Object detected: {object_detected}")
            logger.info(f"   - Height match: {height_match}")
            logger.info(f"   - Distance match: {distance_match}")
            logger.info(f"   - Criteria met: {object_criteria_met}")
            
            # Check LLM result for action
            action = llm_result.get("action")
            if action:
                action_lower = self.normalise_action(action)
                logger.info(f"🎯 Action detected: {action_lower}")
                
                # Map action + object detection combination
                if action_lower == "incision":
                    if object_criteria_met:
                        base_command = self.command_map.get("incision_with_object", "a1")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 Incision + Object → {command}")
                    else:
                        base_command = self.command_map.get("incision", "a0")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 Incision only → {command}")
                    return command
                
                elif action_lower == "stitch":
                    if object_criteria_met:
                        base_command = self.command_map.get("stitch_with_object", "b1")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 Stitch + Object → {command}")
                    else:
                        base_command = self.command_map.get("stitch", "b0")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 Stitch only → {command}")
                    return command
                
                elif action_lower in ["grasp", "cut"]:
                    if object_criteria_met:
                        base_command = self.command_map.get(f"{action_lower}_with_object", f"{action_lower[0]}1")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 {action_lower} + Object → {command}")
                    else:
                        base_command = self.command_map.get(action_lower, f"{action_lower[0]}0")
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 {action_lower} only → {command}")
                    return command
                
                else:
                    # Generic action mapping; honour an "<action>_with_object" variant when one exists
                    base_command = None
                    if object_criteria_met:
                        base_command = self.command_map.get(f"{action_lower}_with_object")
                    base_command = base_command or self.command_map.get(action_lower)
                    if base_command:
                        command = f"{base_command}{handedness_suffix}"
                        logger.info(f"🎯 Generic action '{action_lower}' → {command}")
                        return command
            
            # No valid action found - send 'x' instead of object detection command
            logger.warning("⚠️ No valid action found in mapping - sending 'x'")
            return "x"
            
        except Exception as e:
            logger.error(f"❌ Command mapping error: {e}")
            return "x"  # Default no-op command
    
    def normalise_action(self, action: str) -> str:
        """Lower-case and map synonyms (suture -> stitch, hold -> grasp) onto known actions."""
        key = str(action).strip().lower()
        return self.synonyms.get(key, key)

    def get_command_for_action(self, action: str) -> Optional[str]:
        """
        Get command for a specific action.
        
        Args:
            action: The action to map
            
        Returns:
            Command string or None if not found
        """
        return self.command_map.get(action.lower())
    
    def get_all_commands(self) -> Dict[str, str]:
        """
        Get all available commands.
        
        Returns:
            Dictionary of all command mappings
        """
        return self.command_map.copy()
    
    def add_command_mapping(self, action: str, command: str) -> None:
        """
        Add a new command mapping.
        
        Args:
            action: The action to map
            command: The command string
        """
        self.command_map[action.lower()] = command
        logger.info(f"✅ Added command mapping: {action} -> {command}")
    
    def validate_command(self, command: str) -> bool:
        """
        Validate if a command is valid.
        
        Args:
            command: The command to validate
            
        Returns:
            True if valid, False otherwise
        """
        valid_commands = set(self.command_map.values())
        return command in valid_commands
    
    def add_action_mapping(self, action: str, command_without_object: str, command_with_object: str = None) -> None:
        """
        Add a new action mapping with optional object detection variants.
        
        Args:
            action: The action name (e.g., "grasp", "cut")
            command_without_object: Command to send when no object detected
            command_with_object: Command to send when object detected (optional)
        """
        self.command_map[action.lower()] = command_without_object
        
        if command_with_object:
            self.command_map[f"{action.lower()}_with_object"] = command_with_object
        
        logger.info(f"✅ Added action mapping: {action} → {command_without_object}")
        if command_with_object:
            logger.info(f"✅ Added action mapping: {action}_with_object → {command_with_object}")
    
    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all command mappings including action combinations.
        
        Returns:
            Dictionary of all mappings
        """
        return self.command_map.copy()
