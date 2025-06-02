# Enhanced TurboTalk AI - Science for Society
# Multi-Stage AI Reasoning with Web Scraping Integration
# Developed by Rango Productions

import json
import logging
import os
import requests
import threading
import webbrowser
import uuid
import re
import time
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from colorama import init
from termcolor import colored
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin, urlparse
import html5lib

# Initialize colorama for cross-platform compatibility
init(autoreset=True)

class Config:
    """Enhanced Configuration class for TurboTalk AI"""
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
    LOG_FILE = "turbotalk_enhanced.log"
    LOG_MAX_SIZE = 1 * 1024 * 1024  # 1 MB
    LOG_BACKUP_COUNT = 5
    
    # Web Scraping Configuration
    WEB_SEARCH_ENGINES = [
        "https://www.google.com/search?q={query}",
        "https://duckduckgo.com/html/?q={query}",
        "https://www.bing.com/search?q={query}"
    ]
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    
    # AI Processing Configuration
    MAX_WEB_RESULTS = 5
    MAX_CONTENT_LENGTH = 1000
    THINKING_DELAY_RANGE = (1, 3)  # seconds
    TYPING_SPEED_RANGE = (0.5, 2.5)  # characters per second

class WebScraper:
    """Advanced web scraping with intelligent content extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger('WebScraper')
        self.session = requests.Session()
        self.headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    def search_web(self, query, max_results=5):
        """Perform web search and extract relevant content"""
        try:
            search_results = []
            
            # Encode query for URL
            encoded_query = quote_plus(query)
            
            # Try different search engines
            for search_engine in Config.WEB_SEARCH_ENGINES[:2]:  # Use first 2 engines
                try:
                    search_url = search_engine.format(query=encoded_query)
                    self.logger.info(f"Searching: {search_url}")
                    
                    response = self.session.get(search_url, timeout=10)
                    if response.status_code == 200:
                        results = self._extract_search_results(response.text, search_engine)
                        search_results.extend(results)
                        
                        if len(search_results) >= max_results:
                            break
                            
                except Exception as e:
                    self.logger.warning(f"Search engine failed: {str(e)}")
                    continue
            
            # Get content from top results
            content_results = []
            for result in search_results[:max_results]:
                content = self._extract_page_content(result['url'])
                if content:
                    content_results.append({
                        'title': result['title'],
                        'url': result['url'],
                        'content': content[:Config.MAX_CONTENT_LENGTH]
                    })
            
            return content_results
            
        except Exception as e:
            self.logger.error(f"Web search failed: {str(e)}")
            return []
    
    def _extract_search_results(self, html, search_engine):
        """Extract search results from search engine HTML"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            if 'google.com' in search_engine:
                # Google search results
                for result in soup.find_all('div', class_='g')[:5]:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href')
                        
                        if url and not url.startswith('/'):
                            results.append({'title': title, 'url': url})
                            
            elif 'duckduckgo.com' in search_engine:
                # DuckDuckGo search results
                for result in soup.find_all('a', class_='result__a')[:5]:
                    title = result.get_text(strip=True)
                    url = result.get('href')
                    
                    if title and url:
                        results.append({'title': title, 'url': url})
                        
            elif 'bing.com' in search_engine:
                # Bing search results
                for result in soup.find_all('h2')[:5]:
                    link_elem = result.find('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        url = link_elem.get('href')
                        
                        if title and url:
                            results.append({'title': title, 'url': url})
            
        except Exception as e:
            self.logger.warning(f"Failed to extract search results: {str(e)}")
        
        return results
    
    def _extract_page_content(self, url):
        """Extract main content from a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                
                # Try to find main content
                content_selectors = [
                    'article', 'main', '.content', '.post-content', 
                    '.entry-content', '.article-body', '#content'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = elements[0].get_text(strip=True, separator=' ')
                        break
                
                # Fallback to body content
                if not content:
                    body = soup.find('body')
                    if body:
                        content = body.get_text(strip=True, separator=' ')
                
                # Clean and truncate content
                content = re.sub(r'\s+', ' ', content)
                return content[:Config.MAX_CONTENT_LENGTH]
                
        except Exception as e:
            self.logger.warning(f"Failed to extract content from {url}: {str(e)}")
        
        return ""

class AIReasoningPipeline:
    """Multi-stage AI reasoning and processing pipeline"""
    
    def __init__(self, chat_api, web_scraper):
        self.chat_api = chat_api
        self.web_scraper = web_scraper
        self.logger = logging.getLogger('AIReasoningPipeline')
    
    def process_request(self, user_message, session_id, conversation_history):
        """Execute the complete 5-stage AI reasoning pipeline"""
        
        # Stage 1: Think and Plan
        thinking_result = self._stage_1_think_and_plan(user_message, session_id, conversation_history)
        
        # Stage 2: Summarize Thinking
        summary_result = self._stage_2_summarize_thinking(thinking_result, session_id, conversation_history)
        
        # Stage 3: Generate Search Prompt
        search_prompt = self._stage_3_generate_search_prompt(summary_result, session_id, conversation_history)
        
        # Stage 4: Generate Search Topics
        search_topics = self._stage_4_generate_search_topics(summary_result, session_id, conversation_history)
        
        # Stage 5: Web Search and Final Response
        final_response = self._stage_5_final_response(
            user_message, summary_result, search_prompt, search_topics, session_id, conversation_history
        )
        
        return {
            'thinking_summary': summary_result,
            'final_response': final_response
        }
    
    def _stage_1_think_and_plan(self, user_message, session_id, conversation_history):
        """Stage 1: Analyze user request and create response structure plan"""
        
        prompt = f"""
        You are TurboTalk AI's internal thinking processor. Analyze this user request deeply and create a structured response plan.
        
        User Request: "{user_message}"
        
        Think about:
        1. What is the user really asking for?
        2. What type of response would be most helpful?
        3. What information might I need to gather?
        4. How should I structure my response?
        5. Which of these categories does this fall into:
           - Educational Science (physics, chemistry, biology, mathematics, technology)
           - Environmental Awareness (climate, sustainability, conservation, green energy)
           - Health & Wellness (medical info, mental health, nutrition, fitness)
           - Community Problem Solving (social issues, local problems, civic engagement)
           - General Knowledge/Other
        
        Create a clear thinking process and response structure plan. Be thorough but concise.
        """
        
        return self.chat_api.send_request(prompt, conversation_history, session_id)
    
    def _stage_2_summarize_thinking(self, thinking_result, session_id, conversation_history):
        """Stage 2: Summarize the thinking process"""
        
        prompt = f"""
        You are TurboTalk AI's thinking summarizer. Take this detailed thinking process and create a clear, concise summary.
        
        Detailed Thinking: "{thinking_result}"
        
        Create a brief summary that captures:
        1. The main user intent
        2. The type of information needed
        3. The planned response approach
        4. Key focus areas
        
        Keep it under 100 words but comprehensive.
        """
        
        return self.chat_api.send_request(prompt, conversation_history, session_id)
    
    def _stage_3_generate_search_prompt(self, summary_result, session_id, conversation_history):
        """Stage 3: Generate optimized search prompt"""
        
        prompt = f"""
        You are TurboTalk AI's search prompt generator. Based on this thinking summary, create an optimized search query.
        
        Thinking Summary: "{summary_result}"
        
        Generate a single, focused search query that would help gather the most relevant information.
        Make it specific, clear, and likely to return quality results.
        
        Return ONLY the search query, nothing else.
        """
        
        return self.chat_api.send_request(prompt, conversation_history, session_id)
    
    def _stage_4_generate_search_topics(self, summary_result, session_id, conversation_history):
        """Stage 4: Generate specific web search topics"""
        
        prompt = f"""
        You are TurboTalk AI's search topic generator. Based on this thinking summary, suggest 3-5 specific topics to search for.
        
        Thinking Summary: "{summary_result}"
        
        Generate 3-5 specific search topics that would provide comprehensive information.
        Each topic should be 2-4 words, focused and searchable.
        
        Format as: topic1, topic2, topic3, topic4, topic5
        """
        
        topics_response = self.chat_api.send_request(prompt, conversation_history, session_id)
        
        # Parse topics
        topics = [topic.strip() for topic in topics_response.split(',') if topic.strip()]
        return topics[:5]  # Limit to 5 topics
    
    def _stage_5_final_response(self, user_message, summary_result, search_prompt, search_topics, session_id, conversation_history):
        """Stage 5: Perform web search and generate final response"""
        
        # Perform web searches
        all_web_content = []
        
        # Search using generated prompt
        if search_prompt.strip():
            web_results = self.web_scraper.search_web(search_prompt.strip(), max_results=3)
            all_web_content.extend(web_results)
        
        # Search using individual topics
        for topic in search_topics:
            if topic.strip():
                web_results = self.web_scraper.search_web(topic.strip(), max_results=2)
                all_web_content.extend(web_results)
        
        # Prepare web content summary
        web_summary = ""
        if all_web_content:
            web_summary = "\n\nRelevant Web Information:\n"
            for i, result in enumerate(all_web_content[:5], 1):
                web_summary += f"{i}. {result['title']}: {result['content'][:200]}...\n"
        
        # Generate final response
        final_prompt = f"""
        You are TurboTalk AI, developed by Rango Productions, created by Rushi Bhavinkumar Soni (CEO and Founder).
        
        User Question: "{user_message}"
        
        Your Thinking Summary: "{summary_result}"
        
        {web_summary}
        
        Instructions:
        1. Answer as TurboTalk AI from Rango Productions
        2. If asked about your location/country, say you're from India
        3. If asked about headquarters/physical location, say "I don't have physical access to specific building locations"
        4. DO NOT introduce yourself unless specifically asked
        5. Provide comprehensive, helpful answers with no length restrictions
        6. Use the web information to enhance your response
        7. Focus on being helpful for Science for Society themes
        8. Cover educational, environmental, health, or community aspects when relevant
        
        Provide a complete, informative response that helps solve the user's query.
        """
        
        return self.chat_api.send_request(final_prompt, conversation_history, session_id)

class ConversationManager:
    """Enhanced conversation management with dual output support"""
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
                threading.Event().wait(60)

class ChatAPI:
    """Enhanced API communication with better error handling"""
    def __init__(self):
        self.logger = logging.getLogger('ChatAPI')
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": random.choice(Config.USER_AGENTS),
            "Accept": "*/*",
            "Accept-Encoding": "Identity",
        }

    def send_request(self, inputs, conversation_history, session_id):
        """Send request to the API and process response with fallback"""
        formatted_history = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in conversation_history[-10:]  # Keep last 10 messages for context
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
                elif response.status_code in (401, 403, 429):
                    self.logger.warning(f"Attempt {attempt + 1}: Status {response.status_code}")
                    if attempt == Config.MAX_RETRIES - 1:
                        # Fallback to local processing
                        return self._fallback_response(inputs, conversation_history)
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    if attempt == Config.MAX_RETRIES - 1:
                        return self._fallback_response(inputs, conversation_history)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {str(e)}")
                if attempt == Config.MAX_RETRIES - 1:
                    return self._fallback_response(inputs, conversation_history)

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
    """Configure enhanced logging for the application"""
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

# Initialize enhanced components
setup_logging()
conversation_manager = ConversationManager()
chat_api = ChatAPI()
web_scraper = WebScraper()
ai_pipeline = AIReasoningPipeline(chat_api, web_scraper)
logger = logging.getLogger('TurboTalkApp')

@app.route('/')
def index():
    """Route for the main page"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"New session created: {session['session_id'][:8]}...")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat route with multi-stage AI processing"""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        user_message = request.json.get('message', '').strip()

        if not user_message:
            logger.warning(f"Invalid input: {request.json}")
            return jsonify({"error": "Please provide a message."}), 400

        logger.info(f"Processing request: {user_message[:50]}...")
        
        # Get conversation history
        history = conversation_manager.get_history(session_id)
        
        # Process through AI reasoning pipeline
        result = ai_pipeline.process_request(user_message, session_id, history)
        
        # Add user message to history
        conversation_manager.add_message(session_id, user_message, Config.BOT_ROLE)
        
        # Add bot response to history
        conversation_manager.add_message(session_id, result['final_response'], Config.CHAT_HISTORY_BOT_ROLE)
        
        return jsonify({
            "thinking_summary": result['thinking_summary'],
            "final_response": result['final_response']
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "An error occurred. Please try again."}), 500

def open_browser():
    """Open the browser when the application starts"""
    try:
        webbrowser.open("http://127.0.0.1:8080")
    except Exception as e:
        logger.error(f"Error opening browser: {str(e)}")

if __name__ == '__main__':
    try:
        logger.info("Starting Enhanced TurboTalk AI...")
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
