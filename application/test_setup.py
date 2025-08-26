#!/usr/bin/env python3
"""
Test script to verify the Surgical Assistant setup.
Run this script to check if all dependencies and services are working.
"""

import sys
import os
import importlib

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test if all required packages can be imported."""
    print("🔍 Testing package imports...")
    
    packages = [
        'flask',
        'flask_cors', 
        'python-dotenv',
        'requests',
        'openai',
        'langchain',
        'langchain_openai',
        'langchain_ollama',
        'pydantic',
        'cv2',
        'numpy'
    ]
    
    failed_imports = []
    
    for package in packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'python-dotenv':
                import dotenv
            else:
                importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError as e:
            print(f"   ❌ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("   ✅ All packages imported successfully")
        return True

def test_config():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    try:
        from backend.config import Config
        Config.validate_config()
        print("   ✅ Configuration loaded successfully")
        print(f"   - LLM Provider: {Config.LLM_PROVIDER}")
        print(f"   - LLM Model: {Config.LLM_MODEL}")
        print(f"   - Use Camera: {Config.USE_CAMERA}")
        print(f"   - Use ESP32: {Config.USE_ESP32}")
        return True
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def test_services():
    """Test service initialization."""
    print("\n🔍 Testing services...")
    
    try:
        from backend.services import LLMService, CameraService, CommandService, ESP32Service
        
        # Test LLM service
        try:
            llm = LLMService()
            print("   ✅ LLM Service initialized")
        except Exception as e:
            print(f"   ⚠️ LLM Service warning: {e}")
        
        # Test Camera service
        try:
            camera = CameraService()
            print("   ✅ Camera Service initialized")
        except Exception as e:
            print(f"   ⚠️ Camera Service warning: {e}")
        
        # Test Command service
        try:
            command = CommandService()
            print("   ✅ Command Service initialized")
        except Exception as e:
            print(f"   ❌ Command Service error: {e}")
            return False
        
        # Test ESP32 service
        try:
            esp32 = ESP32Service()
            print("   ✅ ESP32 Service initialized")
        except Exception as e:
            print(f"   ⚠️ ESP32 Service warning: {e}")
        
        return True
    except Exception as e:
        print(f"   ❌ Service initialization error: {e}")
        return False

def test_flask_app():
    """Test Flask app creation."""
    print("\n🔍 Testing Flask application...")
    
    try:
        from backend.app import create_app
        app = create_app()
        print("   ✅ Flask application created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Flask application error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Surgical Assistant Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_services,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("   python run.py")
        print("\nOr:")
        print("   python backend/app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Copy env.example to .env and configure it")
        print("   3. Check your API keys and network connection")
        sys.exit(1)

if __name__ == '__main__':
    main()

