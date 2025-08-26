#!/usr/bin/env python3
"""
Test script to verify handedness detection and command generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.command_service import CommandService
from backend.services.llm_service import LLMService

def test_handedness_commands():
    """Test command generation with different handedness values."""
    
    print("🧪 Testing Handedness Command Generation")
    print("=" * 50)
    
    # Initialize services
    command_service = CommandService()
    llm_service = LLMService()
    
    # Test cases
    test_cases = [
        {
            "instruction": "hi sarath, you can start the incision",
            "expected_handedness": "right",
            "expected_base_command": "a0"
        },
        {
            "instruction": "kiran, please stitch the wound",
            "expected_handedness": "left", 
            "expected_base_command": "b0"
        },
        {
            "instruction": "sarath, use the forceps to grasp the tissue",
            "expected_handedness": "right",
            "expected_base_command": "d0"
        },
        {
            "instruction": "kiran, make an incision with the scalpel",
            "expected_handedness": "left",
            "expected_base_command": "a0"
        }
    ]
    
    # Mock detection data
    mock_detection = {
        "object_detected": False,
        "height_match": False,
        "distance_match": False
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['instruction']}")
        print(f"   Expected handedness: {test_case['expected_handedness']}")
        print(f"   Expected base command: {test_case['expected_base_command']}")
        
        try:
            # Process instruction with LLM
            llm_result = llm_service.process_instruction(test_case['instruction'])
            
            if llm_result.get('error'):
                print(f"   ❌ LLM Error: {llm_result['error']}")
                continue
                
            print(f"   ✅ LLM Result: {llm_result}")
            
            # Generate command
            command = command_service.map_to_command(llm_result, mock_detection)
            
            # Verify handedness
            detected_handedness = llm_result.get('handedness', 'unknown')
            expected_suffix = 'l' if test_case['expected_handedness'] == 'left' else 'r'
            expected_command = f"{test_case['expected_base_command']}{expected_suffix}"
            
            print(f"   🎯 Generated Command: {command}")
            print(f"   🤚 Detected Handedness: {detected_handedness}")
            
            if command == expected_command:
                print(f"   ✅ PASS: Command matches expected {expected_command}")
            else:
                print(f"   ❌ FAIL: Expected {expected_command}, got {command}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🧪 Testing Object Detection with Handedness")
    print("=" * 50)
    
    # Test with object detection
    mock_detection_with_object = {
        "object_detected": True,
        "height_match": True,
        "distance_match": True
    }
    
    # Test incision with object for both handedness
    test_llm_results = [
        {
            "action": "incision",
            "handedness": "left",
            "tool": "scalpel"
        },
        {
            "action": "incision", 
            "handedness": "right",
            "tool": "scalpel"
        },
        {
            "action": "stitch",
            "handedness": "left",
            "tool": "scissors"
        },
        {
            "action": "stitch",
            "handedness": "right", 
            "tool": "scissors"
        }
    ]
    
    for i, llm_result in enumerate(test_llm_results, 1):
        print(f"\n📝 Object Detection Test {i}: {llm_result['action']} ({llm_result['handedness']})")
        
        command = command_service.map_to_command(llm_result, mock_detection_with_object)
        expected_suffix = 'l' if llm_result['handedness'] == 'left' else 'r'
        expected_base = 'a1' if llm_result['action'] == 'incision' else 'b1'
        expected_command = f"{expected_base}{expected_suffix}"
        
        print(f"   🎯 Generated Command: {command}")
        print(f"   🤚 Handedness: {llm_result['handedness']}")
        
        if command == expected_command:
            print(f"   ✅ PASS: Command matches expected {expected_command}")
        else:
            print(f"   ❌ FAIL: Expected {expected_command}, got {command}")
    
    print("\n" + "=" * 50)
    print("🧪 Testing No Action Detection (should return 'x')")
    print("=" * 50)
    
    # Test with no action detected
    test_no_action = {
        "action": None,
        "handedness": "right",
        "tool": None
    }
    
    command = command_service.map_to_command(test_no_action, mock_detection)
    print(f"📝 No Action Test: {test_no_action}")
    print(f"   🎯 Generated Command: {command}")
    
    if command == "x":
        print(f"   ✅ PASS: No action correctly returns 'x'")
    else:
        print(f"   ❌ FAIL: Expected 'x', got {command}")

if __name__ == "__main__":
    test_handedness_commands()
