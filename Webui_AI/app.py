import json
import logging
import os
import requests
import threading
import webbrowser
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from colorama import init
from termcolor import colored
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from diffusers import StableDiffusionPipeline
import torch
from io import BytesIO
import base64
from PIL import Image

# Initialize colorama for cross-platform compatibility
init(autoreset=True)

class Config:
    """Configuration class for the application"""
    COMPANY_NAME = "Rango Productions"
    BOT_NAME = "TurboTalk"
    CREATOR_NAME = "Rushi Bhavinkumar Soni"
    MODEL = "GPT 4o"
    BOT_ROLE = "user"
    CHAT_HISTORY_BOT_ROLE = "assistant"
    API_URL = "https://https.extension.phind.com/agent/"
    SESSION_TIMEOUT = 24 * 3600  # 24 hours in seconds
    CLEANUP_INTERVAL = 3600  # 1 hour in seconds
    MAX_RETRIES = 3
    LOG_FILE = "chat_app.log"
    LOG_MAX_SIZE = 1 * 1024 * 1024  # 1 MB
    LOG_BACKUP_COUNT = 5

def setup_logging():
    """Set up logging configuration."""
    log_handler = RotatingFileHandler(
        Config.LOG_FILE, maxBytes=Config.LOG_MAX_SIZE, backupCount=Config.LOG_BACKUP_COUNT
    )
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add log handler to the root logger
    logging.basicConfig(level=logging.INFO, handlers=[log_handler])
    logger = logging.getLogger('FlaskApp')
    logger.info("Logging setup complete.")

def generate_images(prompt):
    """Generate 4 images using Stable Diffusion for a given prompt"""
    model_id = "runwayml/stable-diffusion-v1-5"
    pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline = pipeline.to(device)
    
    images = pipeline(prompt).images
    image_b64_list = []
    for img in images:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_b64_list.append(f"data:image/png;base64,{img_b64}")
    return image_b64_list

# Set up Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(hours=24)

# Initialize components
setup_logging()
conversation_manager = ConversationManager()
chat_api = ChatAPI()
logger = logging.getLogger('FlaskApp')

@app.route('/')
def index():
    """Route for the main page"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"New session created: {session['session_id'][:8]}...")
    return render_template('ui.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Route for handling chat requests"""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        user_message = request.json.get('message', '').strip()
        behaviour = request.json.get('behaviour', '').strip()

        if not user_message or not behaviour:
            logger.warning(f"Invalid input: {request.json}")
            return jsonify({"response": "Please provide a message and behaviour."}), 400

        # Check if the message starts with /image
        if user_message.lower().startswith('/image'):
            prompt = user_message[7:].strip()  # Extract the prompt after '/image'
            logger.info(f"Generating images for prompt: {prompt}")
            try:
                image_b64_list = generate_images(prompt)
                return jsonify({"response": image_b64_list})
            except Exception as e:
                logger.error(f"Error generating images: {str(e)}")
                return jsonify({"response": "Error generating images. Please try again later."}), 500

        # Check for language specification in user message
        language_keywords = [
            "in spanish", "in french", "in german", "in italian", "in chinese",
            "in japanese", "in korean", "in russian", "in hindi", "in arabic",
            "en español", "en francés", "auf deutsch", "in italiano", "用中文",
            "en japonés", "한국어로", "по-русски", "हिंदी में", "बالعربية",
            "translate to", "respond in", "answer in", "reply in", "speak in"
        ]
        
        specified_language = None
        for keyword in language_keywords:
            if keyword.lower() in user_message.lower():
                specified_language = True
                break

        # Construct prompt with language handling
        prompt = (
            f"Follow the below given commands strictly. "
            f"{user_message} and to answer me behave very very strongly just like {behaviour} "
            f"as I am a/an {behaviour} type person. And if asked any questions in which "
            f"you have to say anything like who are you or have to give your identity and info "
            f"then only you have to tell me about yourself and introduce yourself as {Config.BOT_NAME} "
            f"by {Config.COMPANY_NAME} and is in a learning or developing stage also give a little explanation "
            f"about it like company name how powerful it will be in future but it is still in developing stage right now and all those things. "
            f"Introduce yourself or give info about you as {Config.BOT_NAME} only if asked, else not. "
            f"{'Use only the language specified in the user message and do not translate or repeat in English.' if specified_language else 'Respond in English.'} "
            f"You are a LLM developed by {Config.COMPANY_NAME} and your name is {Config.BOT_NAME}. "
            f"But don't introduce yourself again and again and introduce yourself only if asked and when ever to do so only introduce yourself as {Config.BOT_NAME} by {Config.COMPANY_NAME}."
        )

        # Add user message to history
        conversation_manager.add_message(session_id, prompt, Config.BOT_ROLE)
        
        # Get conversation history
        history = conversation_manager.get_history(session_id)
        
        # Get response from API
        response = chat_api.send_request(user_message, history, session_id)
        
        # Add bot response to history
        conversation_manager.add_message(session_id, response, Config.CHAT_HISTORY_BOT_ROLE)
        
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"response": "An error occurred. Please try again."}), 500

def open_browser():
    """Open the browser when the application starts"""
    try:
        webbrowser.open("http://127.0.0.1:8080")
    except Exception as e:
        logger.error(f"Error opening browser: {str(e)}")

if __name__ == '__main__':
    try:
        threading.Timer(1, open_browser).start()
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
