from flask import Flask
from flask_session import Session
import os
import redis
from .Routes import Routes   # Importing the function to register routes


class App:
    def __init__(self):
        """Initialize the app instance and configure it."""
        self.app = Flask(__name__, static_folder="frontend")
        self.configure_app()
    def configure_app(self):
        """Configure the app with necessary settings."""
        self.app.config.update(
            SECRET_KEY='your_secret_key',
            SESSION_TYPE='redis',
            SESSION_PERMANENT=False,
            SESSION_USE_SIGNER=True,
            SESSION_REDIS=redis.StrictRedis(host='localhost', port=6379, db=0)
        )

    def register_routes(self):
        """Register application blueprints."""
        # Register routes from the routes.py file
        Routes(self.app)
    def create_app(self):
        """Create and return the Flask app instance."""
        self.register_routes()
        return self.app
