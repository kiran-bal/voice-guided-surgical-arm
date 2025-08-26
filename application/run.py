#!/usr/bin/env python3
"""
Launcher script for the Surgical Assistant Flask application.
Run this script from the application directory to start the server.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == '__main__':
    from backend.app import app, Config
    
    print("🚀 Starting Surgical Assistant Flask Application")
    print(f"   - Host: {Config.HOST}")
    print(f"   - Port: {Config.PORT}")
    print(f"   - Debug: {Config.DEBUG}")
    print(f"   - Frontend: http://{Config.HOST}:{Config.PORT}")
    print(f"   - API: http://{Config.HOST}:{Config.PORT}/api")
    print("   - Press Ctrl+C to stop the server")
    print()
    
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
