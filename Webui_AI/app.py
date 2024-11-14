import webbrowser
from flask import Flask, render_template, request, jsonify
import json
import requests
import logging
import threading

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Define your company and bot names
company_name = "Rango Productions"
bot_name = "TurboTalk"
my_name = "Rushi Bhavinkumar Soni"
model = "GPT 4o"

# Define variables for bot information
bot_role = "user"  # This is the bot's role in the interaction
chat_history_bot_role = "assistant"  # This is the role of the bot in the conversation history

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('ui.html')


def prompt_with_context(inputs, conversation_history):
    url = "https://https.extension.phind.com/agent/"  # API endpoint
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "",
        "Accept": "*/*",
        "Accept-Encoding": "Identity",
    }

    # Payload with conversation history
    payload = {
        "additional_extension_context": "",
        "allow_magic_buttons": True,
        "is_vscode_extension": True,
        "message_history": conversation_history,
        "requested_model": model,
        "user_input": inputs,  # Pass the actual user input
    }

    # Send POST request to the API
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:  # If the response is successful
        response_content = response.content
        # Split response content into parts (by line breaks)
        lines = response_content.decode("utf-8").split("\r\n\r\n")
        content_values = []
        for line in lines:
            try:
                data = json.loads(line.split("data: ")[1])  # Parse each part
                choices = data.get("choices", [])
                for choice in choices:
                    content = choice.get("delta", {}).get("content")  # Extract content
                    if content:
                        content_values.append(content)
            except IndexError:
                pass
        return "".join(content_values)  # Return the response as a string

    elif response.status_code == 401 or response.status_code == 429:  # If error occurs (unauthorized or rate limit)
        logging.warning(f"Error: {response.status_code}, Trying again.")
        return prompt_with_context(inputs, conversation_history)  # Retry the request

    else:  # Handle other errors
        return f"Error: {response.status_code}, {response.text}"


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    behaviour = request.json.get('behaviour')

    logging.info("User Message: %s, Behaviour: %s", user_message, behaviour)

    # Input validation
    if not user_message or not behaviour:
        logging.warning("Invalid input: %s", request.json)
        return jsonify({"response": "Invalid input."}), 400

    # Initialize or retrieve conversation history from session or memory
    if not hasattr(chat, 'conversation_history'):
        chat.conversation_history = []  # Initialize if not present
    
    # Construct the AI's prompt based on the user input and behaviour
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
        f"You are a LLM developed by {company_name} and your name is {bot_name}."
        f"But don't introduce yourself again and again and introduce yourself only if asked and when ever to do so only introduce yourself as {bot_name} by {company_name}."
        f"Always give direct answers, and never ever tell me that your purpose is to assist with complex programming tasks, technical inquiries, and information seeking within the context of a VSCode environment instead just tell that your purpose is to assist me in almost every possible way."
        f"Don't include any of these commands in the output, and if anyone asks I am Founder/CEO of the company {company_name}, my name is {my_name}."
    )

    # Add user input to the conversation history
    chat.conversation_history.append({"content": content, "role": bot_role})

    try:
        # Use the prompt function to get the response with context
        bot_response = prompt_with_context(user_message, chat.conversation_history)

    except Exception as e:
        logging.error("Error during chat completion: %s", str(e))
        bot_response = "There was a problem while processing your input. Please try again later."

    # Add assistant response to the conversation history
    chat.conversation_history.append({"content": bot_response, "role": chat_history_bot_role})

    return jsonify({"response": bot_response})


def open_browser():
    webbrowser.open("http://127.0.0.1:8080")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()  # Open the browser after a short delay
    app.run(host='0.0.0.0', port=8080, debug=False)
