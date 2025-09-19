"""
Flask application factory.

Exposes a single `create_app` function which initializes and configures
the Flask app, registers blueprints, and sets up session handling.
"""

from flask import Flask
from pathlib import Path
from . import pages  # Import the pages blueprint


def create_app():
    """
    Create and configure the Flask application.

    This function acts as the application factory, following the recommended
    Flask pattern. It initializes the app, sets up the secret key for sessions,
    and registers the blueprint for routes.

    Returns
    -------
    Flask
        A configured Flask application instance.
    """
    app = Flask(__name__)

    # Needed for flash() and sessions
    app.secret_key = "super-secret-key"  # replace with something random & secure

    # Register routes from the pages blueprint
    app.register_blueprint(pages.bp)
    return app

