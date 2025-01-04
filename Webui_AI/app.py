
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

class ConversationManager:
    """Manages conversation histories for different sessions"""
    def __init__(self):
        self.conversations = {}
        self.session_map = {}
        self.cleanup_interval = Config.CLEANUP_INTERVAL
        self.session_timeout = Config.SESSION_TIMEOUT
        self.logger = logging.getLogger('ConversationManager')
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_old_sessions, daemon=True)
        cleanup_thread.start()
    
    def get_conversation_id(self, session_id):
        """Get or create a conversation ID for a session"""
        if session_id not in self.session_map:
            conv_id = str(uuid.uuid4())
            self.session_map[session_id] = conv_id
            self.conversations[conv_id] = {
                'history': [],
                'last_access': datetime.now(),
                'session_id': session_id
            }
            self.logger.info(f"Created new conversation for session {session_id[:8]}...")
        return self.session_map[session_id]
    
    def add_message(self, session_id, message, role):
        """Add a message to the conversation history"""
        try:
            conv_id = self.get_conversation_id(session_id)
            self.conversations[conv_id]['history'].append({
                'content': message,
                'role': role,
                'timestamp': datetime.now().isoformat()
            })
            self.conversations[conv_id]['last_access'] = datetime.now()
            self.logger.debug(f"Added message for session {session_id[:8]}...")
        except Exception as e:
            self.logger.error(f"Error adding message: {str(e)}")
            raise
    
    def get_history(self, session_id):
        """Get conversation history for a session"""
        try:
            conv_id = self.get_conversation_id(session_id)
            return self.conversations[conv_id]['history']
        except Exception as e:
            self.logger.error(f"Error getting history: {str(e)}")
            return []
    
    def _cleanup_old_sessions(self):
        """Periodically clean up old sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_convs = []
                
                for conv_id, data in self.conversations.items():
                    if (current_time - data['last_access']).total_seconds() > self.session_timeout:
                        expired_convs.append(conv_id)
                        session_id = data['session_id']
                        if session_id in self.session_map:
                            del self.session_map[session_id]
                
                for conv_id in expired_convs:
                    del self.conversations[conv_id]
                    self.logger.info(f"Cleaned up conversation {conv_id[:8]}...")
                
                threading.Event().wait(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
                threading.Event().wait(60)  # Wait a minute before retrying

class ChatAPI:
    """Handles communication with the chat API"""
    def __init__(self):
        self.logger = logging.getLogger('ChatAPI')
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "",
            "Accept": "*/*",
            "Accept-Encoding": "Identity",
        }

    def send_request(self, inputs, conversation_history, session_id):
        """Send request to the API and process response"""
        formatted_history = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in conversation_history
        ]

        payload = {
            "additional_extension_context": "",
            "allow_magic_buttons": True,
            "is_vscode_extension": True,
            "message_history": formatted_history,
            "requested_model": Config.MODEL,
            "user_input": inputs,
        }

        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.post(
                    Config.API_URL,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return self._process_response(response)
                elif response.status_code in (401, 429):
                    self.logger.warning(f"Attempt {attempt + 1}: Status {response.status_code}")
                    if attempt == Config.MAX_RETRIES - 1:
                        return "Server is busy. Please try again later."
                    threading.Event().wait(2 ** attempt)  # Exponential backoff
                else:
                    return f"Error: {response.status_code}"
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {str(e)}")
                if attempt == Config.MAX_RETRIES - 1:
                    return "Network error. Please check your connection."

    def _process_response(self, response):
        """Process the API response"""
        try:
            response_content = response.content
            lines = response_content.decode("utf-8").split("\r\n\r\n")
            content_values = []
            
            for line in lines:
                if line.startswith("data: "):
                    try:
                        data = json.loads(line.split("data: ")[1])
                        choices = data.get("choices", [])
                        for choice in choices:
                            content = choice.get("delta", {}).get("content")
                            if content:
                                content_values.append(content)
                    except json.JSONDecodeError:
                        continue
                        
            return "".join(content_values) or "No response generated."
            
        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return "Error processing response."

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(level=logging.INFO)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join('logs', Config.LOG_FILE),
        maxBytes=Config.LOG_MAX_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add handler to root logger
    logging.getLogger('').addHandler(file_handler)

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

        # Construct prompt
        prompt = (
            f"Follow the below given commands strictly. "
            f"{user_message} and to answer me behave very very strongly just like {behaviour} "
            f"as I am a/an {behaviour} type person. And if asked any questions in which "
            f"you have to say anything like who are you or have to give your identity and info "
            f"then only you have to tell me about yourself and introduce yourself as {Config.BOT_NAME} "
            f"by {Config.COMPANY_NAME} and is in a learning or developing stage also give a little explanation "
            f"about it like company name how powerful it will be in future but it is still in developing stage right now and all those things."
            f"Introduce yourself or give info about you as {Config.BOT_NAME} only if asked, else not."
            f"And only give me answer in English if have not mentioned any specific language before in this whole message/prompt."
            f"You are a LLM developed by {Config.COMPANY_NAME} and your name is {Config.BOT_NAME}."
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
