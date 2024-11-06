from flask import Flask, render_template, request, jsonify
import TurboTalk_Custom

app = Flask(__name__)

def process_message(text):
    """
    Process the incoming text using TurboTalk_Custom to generate responses.
    """
    # Define parameters for TurboTalk
    text = text
    company_name = "Rango Productions"
    bot_name = "Rango AI"
    behaviour = "Friendly"
    content = (
        f"Follow the below given commands strictly. "
        f"{text} and to answer me behave very very strongly just like {behaviour} "
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
    user_message = content
    
    # Generate response using TurboTalk
    TurboTalk_Custom.turbo_talk_instance.give_response(
        company_name,
        bot_name,
        behaviour,
        user_message
    )

    # Get the response
    response = TurboTalk_Custom.turbo_talk_instance.get_response()

    return response

@app.route('/')
def home():
    # Serve index.html from the templates folder
    return render_template('index.html')

@app.route('/process_voice', methods=['POST'])
def process_voice():
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            raise ValueError("No text provided")

        # Get the user's IP address
        user_ip = request.remote_addr
        print(f"User IP: {user_ip}")

        # Process the text and get response
        response = process_message(text)

        # Check if the response is the specific output
        if "BLACKBOX" in response:
            return jsonify({
                'response': "Please re-enter your message after reloading the site ↻.",
                'status': 'error',
                'user_ip': user_ip
            })

        return jsonify({
            'response': response,
            'status': 'success',
            'user_ip': user_ip
        })

    except ValueError as ve:
        return jsonify({
            'response': str(ve),
            'status': 'error'
        }), 400
    except Exception as e:
        print(f"Error: {str(e)}")  # Log the error for debugging
        return jsonify({
            'response': "There was a problem while processing your input. Try again later.",
            'status': 'error'
        }), 500

if __name__ == '__main__':
    # Run the Flask app on all available network interfaces
    app.run(host='0.0.0.0', port=5000, debug=False)
