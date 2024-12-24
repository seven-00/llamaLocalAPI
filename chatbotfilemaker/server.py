from flask import Flask, request, Response, jsonify, send_from_directory, session
import requests
import json
import os
import io
from pypdf import PdfReader
from flask_session import Session  # Import Flask-Session for session management with Redis
import redis
import subprocess

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

def flush_redis_in_wsl():
    try:
        # Command to flush Redis in WSL
        cmd = "wsl redis-cli FLUSHDB"
        process = subprocess.run(cmd, shell=True, check=True, text=True)
        print("Redis database in WSL has been flushed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the WSL command: {e}")

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
        print(f"Making POST request to: {url} with model {model}")
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()  # Check for request errors
            # print(f"Response status code: {response.status_code}")
            for line in response.iter_lines():
                if line:
                    try:
                        json_obj = json.loads(line)  # Parse each chunk
                        # print(f"Received chunk: {json_obj}")  # Print the chunk for debugging
                        yield json_obj  # Yield each chunk of data as it arrives
                    except json.JSONDecodeError:
                        print("Failed to decode JSON from chunk")  # Handle invalid JSON
                        continue  # Ignore lines that are not valid JSON
    except requests.exceptions.RequestException as e:
        # print(f"Error during request: {e}")  # Print error message for debugging
        yield {"error": f"Error communicating with Ollama: {e}"}  # Yield error if request fails


@app.route("/")
def index():
    # Serve the HTML file
    return send_from_directory(app.static_folder, "index.html")

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Store user and bot messages in a session array only after the stream is completed.
    """
    data = request.json
    prompt = data.get("prompt", "")
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400  # Ensure a response is always returned

    # Initialize the session storage for conversation if it doesn't exist
    if 'conversation_history' not in session:
        session['conversation_history'] = []

    # Append the user message to the session conversation history
    session['conversation_history'].append({"role": "user", "message": prompt})

    # Combine session messages into the prompt context
    conversation_history = "\n".join(
        [f"{item['role'].capitalize()}: {item['message']}" for item in session['conversation_history']]
    )
    full_prompt = f"{conversation_history}\n\nUser: {prompt}\nBot:"
    final_bot_message = ""
    def stream_response():
        bot_message = ""
        error_occurred = False
        print("Starting to stream response from Ollama...")  # Debugging start of response stream
    
        for chunk in query_ollama_stream(full_prompt):  # Assuming query_ollama_stream yields chunks
            # print(f"Received chunk: {chunk}")  # Debugging the received chunk
        
            if "error" in chunk:
                print(f"Error received from Ollama: {chunk['error']}")  # Debugging error message from Ollama
                yield json.dumps({"error": chunk["error"]}) + "\n"
                error_occurred = True
                break
        
            if "response" in chunk:
                bot_message += chunk["response"]
                # print(f"Appending message: {chunk['response']}")  # Debugging the message being appended to bot_message
                yield json.dumps(chunk) + "\n"
            global final_bot_message
            final_bot_message = bot_message
    

    # Ensure the function returns a valid response
    print("streaming")
    print(f"Final bot message: {final_bot_message}")  # Debugging the final bot message
    session['conversation_history'].append({"role": "bot", "message": final_bot_message})
    return Response(stream_response(), content_type="application/json")


@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """
    Extract text from a PDF uploaded as raw binary data.
    """
    try:
        # Read the raw binary data from the request
        binary_pdf = request.data

        if not binary_pdf:
            return jsonify({"error": "No binary data received"}), 400

        # Use io.BytesIO to convert the binary data into a file-like object
        pdf_file = io.BytesIO(binary_pdf)

        # Read the PDF using pypdf
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        if not text.strip():
            return jsonify({"error": "Unable to extract text from the PDF"}), 400

        # Optionally store the extracted text in the session
        session['pdf_content'] = text

        # Return the extracted text or process it further
        return jsonify({"message": "PDF text extracted successfully", "content": text}), 200
        # Note: Return only the first 500 characters to avoid sending too much data

    except Exception as e:
        return jsonify({"error": f"Failed to process the PDF: {e}"}), 500

if __name__ == "__main__":
    flush_redis_in_wsl()
    app.run(host="0.0.0.0", port=5000, debug=True)
