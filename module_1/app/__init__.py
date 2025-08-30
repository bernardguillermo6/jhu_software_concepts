from flask import Flask
from pathlib import Path
from app import pages # Import the pages blueprint

def create_app():
    """
    Factory function to create and configure the Flask application.
    """    
    app = Flask(__name__) # Create a new Flask app instance

    app.register_blueprint(pages.bp) # Register the pages blueprint for routing
    return app
