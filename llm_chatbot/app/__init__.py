from flask import Flask
import redis
from .Routes import Routes  # Importing the function to register routes


class App:
    def __init__(self):
        """Initialize the app instance and configure it."""
        self.app = Flask(__name__, static_folder="frontend")
        self.redis_client = None  # Redis client instance
        self.configure_app()

    def configure_app(self):
        """Configure the app with necessary settings and initialize Redis."""


        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    def get_redis_client(self):
        """Expose the Redis client to be used by routes or other components."""
        return self.redis_client

    def register_routes(self):
        """Register application routes."""
        # Pass the app instance and Redis client to routes
        Routes(self.app, self.redis_client)

    def create_app(self):
        """Create and return the Flask app instance."""
        self.register_routes()
        return self.app
