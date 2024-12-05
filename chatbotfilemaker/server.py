from flask import Flask, request, Response, jsonify, send_from_directory
import requests
import json
import os

app = Flask(__name__, static_folder="frontend")  # Specify the folder for static files

def query_ollama_stream(prompt: str, host: str = "http://localhost:11434", model: str = "llama3.2:1b"):
    """
    Stream the response from Ollama API and yield JSON chunks as they.
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
    Stream JSON responses as chunks are received from query_ollama_stream.
    """
    data = request.json
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    def stream_response():
        for chunk in query_ollama_stream(prompt):
            if "error" in chunk:
                yield json.dumps({"error": chunk["error"]}) + "\n"
                break
            yield json.dumps(chunk) + "\n"
    print(Response(stream_response(), content_type="application/json"))

    return Response(stream_response(), content_type="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)

