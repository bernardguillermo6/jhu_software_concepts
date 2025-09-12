from flask import Flask
from pathlib import Path
from app import pages # Import the pages blueprint

def create_app():
    """
    Factory function to create and configure the Flask application.
    """    
    app = Flask(__name__) # Create a new Flask app instance

    # Needed for flash() and sessions
    app.secret_key = "super-secret-key"  # replace with something random & secure

    app.register_blueprint(pages.bp) # Register the pages blueprint for routing
    return app
