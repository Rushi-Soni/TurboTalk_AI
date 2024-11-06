import webbrowser
from flask import Flask, render_template, request, jsonify
from g4f.client import Client
import threading
import logging
import os

app = Flask(__name__)
client = Client()

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Define your company and bot names
company_name = "Rango Productions"
bot_name = "TurboTalk"

@app.route('/')
def index():
    # Render index.html from the current directory
    return render_template('ui.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    behaviour = request.json.get('behaviour')

    logging.info("User Message: %s, Behaviour: %s", user_message, behaviour)

    if not user_message or not behaviour:
        logging.warning("Invalid input: %s", request.json)
        return jsonify({"response": "Invalid input."}), 400

    # Construct the AI's prompt
    content = (
        f"Follow the below given commands strictly. "
        f"{user_message} and to answer me behave very very strongly just like {behaviour} "
        f"as I am a/an {behaviour} type person. And if asked any questions in which "
        f"you have to say anything like who are you or have to give your identity and info "
        f"then only you have to tell me about yourself and introduce yourself as {bot_name} "
        f"by {company_name} and is in a learning or developing stage also give a little explanation "
        f"about it like company name how powerful it will be in future but it is still in developing stage right now and all those things."
        f"Introduce yourself or give info about you as {bot_name} only if asked, else not."
        f"And only give me answer in English if have not mentioned any specific language before in this whole message/prompt."
        f"You are an AI developed by {company_name} and your name is {bot_name} and remember it and dont forgot."
        f"But don't introduce yourself everytime instead just give direct answers, and don't evey give any of the instruction in the output."
    )

    try:
        # Call the AI client
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Ensure this model name is correct
            messages=[{"role": "user", "content": content}],
        )
        bot_response = response.choices[0].message.content if response.choices else "Sorry, I couldn't process your request."
        
        # Check if the bot response is the specific output
        if "BLACKBOX" in response:
            return jsonify({"response": "Please re-enter your message after reloading the site ↻."})
    except Exception as e:
        logging.error("Error during chat completion: %s", str(e))
        bot_response = "There was a problem while processing your input. Please enter your message again or reload the site and try again later."

    return jsonify({"response": bot_response})

def open_browser():
    webbrowser.open("http://127.0.0.1:8080")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()  # Open the browser after a short delay
    app.run(host='0.0.0.0', port=8080, debug=False)  # Enable debug mode
