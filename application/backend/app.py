"""
Main Flask application for the surgical assistant.
Serves both API endpoints and frontend static files.
"""

import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from .config import Config
from .routes import api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__, 
                static_folder='../frontend/static',
                template_folder='../frontend')
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Configure app
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    
    logger.info("✅ Flask application created successfully")
    return app


def serve_frontend():
    """Serve the frontend index.html file."""
    from flask import current_app
    return send_from_directory(current_app.template_folder, 'index.html')


# Create app instance
app = create_app()


# Frontend route
@app.route('/')
def index():
    """Serve the main frontend page."""
    return serve_frontend()


# Static files route
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return {"error": "Not found", "message": "The requested resource was not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return {"error": "Internal server error", "message": "An unexpected error occurred"}, 500


if __name__ == '__main__':
    """Run the Flask application."""
    logger.info("🚀 Starting Surgical Assistant Flask Application")
    logger.info(f"   - Host: {Config.HOST}")
    logger.info(f"   - Port: {Config.PORT}")
    logger.info(f"   - Debug: {Config.DEBUG}")
    logger.info(f"   - Frontend: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"   - API: http://{Config.HOST}:{Config.PORT}/api")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

