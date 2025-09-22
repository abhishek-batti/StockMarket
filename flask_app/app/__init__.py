from flask import Flask
from app.routes.chat import chat_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Enable CORS for the whole app
    CORS(app)

    # Register the chat blueprint with /api prefix
    app.register_blueprint(chat_bp, url_prefix="/api")

    # Return the original Flask app instance
    return app
