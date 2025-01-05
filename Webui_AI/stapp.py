import streamlit as st
import torch
from diffusers import StableDiffusionPipeline
import logging
import uuid
from datetime import datetime
import io
import base64
from PIL import Image
import os
from logging.handlers import RotatingFileHandler

# Configuration
class Config:
    COMPANY_NAME = "Rango Productions"
    BOT_NAME = "TurboTalk"
    CREATOR_NAME = "Rushi Bhavinkumar Soni"
    MODEL = "GPT 4o"
    SESSION_TIMEOUT = 24 * 3600  # 24 hours in seconds
    LOG_FILE = "chat_app.log"
    LOG_MAX_SIZE = 1 * 1024 * 1024  # 1 MB
    LOG_BACKUP_COUNT = 5
    IMAGE_OUTPUT_DIR = "generated_images"

class ImageGenerator:
    def __init__(self):
        self.model_id = "runwayml/stable-diffusion-v1-5"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = None
        self.logger = logging.getLogger('ImageGenerator')
        
    def initialize(self):
        try:
            if self.pipeline is None:
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                self.pipeline = self.pipeline.to(self.device)
            return True
        except Exception as e:
            self.logger.error(f"Error initializing image generator: {str(e)}")
            return False
    
    def generate_images(self, prompt):
        try:
            if not self.initialize():
                return None
                
            images = []
            for _ in range(4):  # Generate 4 images
                image = self.pipeline(prompt).images[0]
                images.append(image)
                
            return images
        except Exception as e:
            self.logger.error(f"Error generating images: {str(e)}")
            return None

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        os.path.join('logs', Config.LOG_FILE),
        maxBytes=Config.LOG_MAX_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    logging.getLogger('').addHandler(file_handler)

def init_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'image_generator' not in st.session_state:
        st.session_state.image_generator = ImageGenerator()

def main():
    setup_logging()
    init_session_state()
    logger = logging.getLogger('StreamlitApp')

    # Set page config
    st.set_page_config(
        page_title="TurboTalk",
        page_icon="🗣️",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stTextInput, .stSelectbox {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 10px;
        }
        .stButton > button {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 15px;
            padding: 10px 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("TurboTalk")
        st.markdown(f"<p style='text-align: center; color: white;'>Powered by {Config.COMPANY_NAME}</p>", unsafe_allow_html=True)

    # Chat interface
    st.markdown("<br>", unsafe_allow_html=True)

    # Behavior selector
    behavior = st.selectbox(
        "Select chat behavior",
        ["🤗 Friendly", "👔 Professional", "😊 Casual", "🎩 Formal", 
         "😄 Humorous", "🎨 Creative", "🔬 Scientific", "📝 Poetic"],
        key="behavior"
    )

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "images" in message:
                st.write(message["content"])
                cols = st.columns(2)
                for idx, img in enumerate(message["images"]):
                    cols[idx % 2].image(img, use_column_width=True)
            else:
                st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Handle image generation
        if prompt.startswith('/img '):
            image_prompt = prompt[5:].strip()
            with st.spinner('Generating images...'):
                images = st.session_state.image_generator.generate_images(image_prompt)
                if images:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Generated images:",
                        "images": images
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Failed to generate images. Please try again."
                    })
        else:
            # Regular chat message
            behavior_text = behavior.split(" ")[1]  # Remove emoji
            prompt_with_behavior = (
                f"Follow the below given commands strictly. "
                f"{prompt} and to answer me behave very very strongly just like {behavior_text} "
                f"as I am a/an {behavior_text} type person."
            )
            
            # Add assistant response
            # Note: In a real implementation, you would integrate with your chat API here
            response = f"This is a sample response in {behavior_text} style. In a real implementation, you would integrate with your chat API here."
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Rerun to update chat display
        st.rerun()

if __name__ == '__main__':
    main()
