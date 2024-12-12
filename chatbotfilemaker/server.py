from flask import Flask, request, Response, jsonify, send_from_directory, session
import requests
import json
import os
import io
from pypdf import PdfReader
from flask_session import Session  # Import Flask-Session for session management with Redis
import redis

app = Flask(__name__, static_folder="frontend")  # Specify the folder for static files

# Set a secret key for session encryption
app.secret_key = 'your_secret_key'  # Make sure to use a secure key in production

# Configure Redis for session storage
app.config['SESSION_TYPE'] = 'redis'  # Use Redis to store session data
app.config['SESSION_PERMANENT'] = False  # Set session to not be permanent by default
app.config['SESSION_USE_SIGNER'] = True  # Enable signing of cookies for security
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)  # Connect to Redis

# Initialize the session extension
Session(app)

def query_ollama_stream(prompt: str, host: str = "http://localhost:11434", model: str = "llama3.2:1b"):
    """
    Stream the response from Ollama API and yield JSON chunks as they arrive.
    """
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
    }

    try:
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        json_obj = json.loads(line)
                        yield json_obj
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.RequestException as e:
        yield {"error": f"Error communicating with Ollama: {e}"}

@app.route("/")
def index():
    # Serve the HTML file
    return send_from_directory(app.static_folder, "index.html")

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Store user messages in a session array and stream responses.
    """
    data = request.json
    prompt = data.get("prompt", "")
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Store the user message in the session (initialize if necessary)
    if 'user_messages' not in session:
        session['user_messages'] = []  # Initialize the array if it doesn't exist

    # Append the user message to the session array
    session['user_messages'].append(prompt)

    # Optional: Limit the array size to the last 10 messages
    if len(session['user_messages']) > 10:
        session['user_messages'].pop(0)  # Remove the oldest message

    # Combine session messages into the prompt context
    conversation_history = "\n".join(session['user_messages'])
    full_prompt = f"{conversation_history}\n\nUser: {prompt}\nBot:"

    # Debugging: Print session data to the command line
    print("Total user messages in session:", session['user_messages'])

    # Stream response from Ollama API
    def stream_response():
        for chunk in query_ollama_stream(full_prompt):
            if "error" in chunk:
                yield json.dumps({"error": chunk["error"]}) + "\n"
                break
            yield json.dumps(chunk) + "\n"
            
    return Response(stream_response(), content_type="application/json")

@app.route('/get-session', methods=['GET'])
def get_session_data():
    """
    Retrieve and return the current session data (user messages).
    """
    user_messages = session.get('user_messages', [])
    
    # Debugging: Print current session state to the console
    print("Current user messages in session:", user_messages)
    
    return jsonify({
        "user_messages": user_messages
    })

@app.route('/clear-session', methods=['GET'])
def clear_session_data():
    """
    Clear the session data and reset the user messages.
    """
    session.clear()  # Clear all session data
    return jsonify({"message": "Session data cleared"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
