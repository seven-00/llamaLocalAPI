import json
import os
from flask import request, Response, jsonify, send_file
from .QueryOllama import QueryOllama
from .PdfExtract import ProcessPdf


class Routes:
    def __init__(self, app, redis_client):
        self.app = app
        self.redis_client = redis_client  # Redis client instance
        self.register_routes()

    def register_routes(self):
        """Register routes using decorators."""
        @self.app.route('/')
        def index():
            """Route to serve the index page."""
            file_path = os.path.join(os.getcwd(), "frontend", "index.html")
            return send_file(file_path)

        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            """Route to handle chat API."""
            data = request.json
            prompt = data.get("prompt", "")

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            # Retrieve conversation history from Redis
            conversation_history = self.redis_client.get(
                'conversation_history')
            if conversation_history:
                conversation_history = json.loads(conversation_history)
            else:
                conversation_history = []

             # Retrieve PDF content from Redis
            pdf_content = self.redis_client.get('pdf_content')
            if pdf_content:
                pdf_section = f"\n\nPDF Content:\n{pdf_content}\n\n"
            else:
                pdf_section = ""  # No PDF content available

            # Append user message to conversation history
            conversation_history.append({"role": "user", "message": prompt})
            self.redis_client.set('conversation_history',
                                json.dumps(conversation_history))

            # Combine PDF content, conversation history, and the prompt
            conversation_history_text = "\n".join(
                [f"{item['role'].capitalize()}: {item['message']}" for item in conversation_history]
            )
            full_prompt = f"{pdf_section}{conversation_history_text}\nUser: {prompt}"

            bot_message = ""  # Initialize bot message

            def stream_response():
                nonlocal bot_message
                query_ollama = QueryOllama()
                for chunk in query_ollama.query_stream(full_prompt):
                    if "error" in chunk:
                        yield json.dumps({"error": chunk["error"]}) + "\n"
                        break

                    if "response" in chunk:
                        bot_message += chunk["response"]
                        yield json.dumps(chunk) + "\n"

            response = Response(stream_response(),
                                content_type="application/json")
            return response

        @self.app.route('/api/upload_pdf', methods=['POST'])
        def upload_pdf():
            """Route to handle PDF upload and text extraction."""
            try:
                binary_pdf = request.data
                if not binary_pdf:
                    return jsonify({"error": "No binary data received"}), 400

                text = ProcessPdf(binary_pdf)
                self.redis_client.set('pdf_content', text)

                return jsonify({
                    "message": "PDF text extracted successfully",
                    "content": text
                }), 200

            except Exception as e:
                return jsonify({"error": f"Failed to process the PDF: {e}"}), 500

        @self.app.route('/api/bot', methods=['POST'])
        def bot_response():
            """Route to accept and log the bot response."""
            data = request.json
            bot_message = data.get('bot_message', '')

            if not bot_message:
                return jsonify({"error": "No bot message provided"}), 400

            # Update conversation history in Redis
            conversation_history = self.redis_client.get(
                'conversation_history')
            if conversation_history:
                conversation_history = json.loads(conversation_history)
            else:
                conversation_history = []

            conversation_history.append(
                {"role": "bot", "message": bot_message})
            self.redis_client.set('conversation_history',
                                  json.dumps(conversation_history))

            return jsonify({"message": "Bot message received"}), 200

        @self.app.route('/api/session', methods=['GET'])
        def session_data():
            """Route to retrieve session-like data."""
            conversation_history = self.redis_client.get(
                'conversation_history')
            if not conversation_history:
                return jsonify({"error": "No session data available"}), 404

            return jsonify(json.loads(conversation_history)), 200
