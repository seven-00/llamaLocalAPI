import json
import os
from flask import request, Response, jsonify, session, send_file
from .QueryOllama import QueryOllama
from .PdfExtract import ProcessPdf


class Routes:
    def __init__(self, app):
        self.app = app
        # Register routes directly using decorators
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

            if 'conversation_history' not in session:
                session['conversation_history'] = []

            session['conversation_history'].append(
                {"role": "user", "message": prompt})

            conversation_history = "\n".join(
                [f"{item['role'].capitalize()}: {item['message']}" for item in session['conversation_history']]
            )
            full_prompt = f"{conversation_history}\n\nUser: {prompt}\nBot:"
            final_bot_message = ""

            def stream_response():
                bot_message = " "

                query_ollama = QueryOllama()
                for chunk in query_ollama.query_stream(full_prompt):
                    if "error" in chunk:
                        yield json.dumps({"error": chunk["error"]}) + "\n"
                        break

                    if "response" in chunk:
                        bot_message += chunk["response"]
                        yield json.dumps(chunk) + "\n"

                nonlocal final_bot_message
                final_bot_message = bot_message

            session['conversation_history'].append(
                {"role": "bot", "message": final_bot_message})
            return Response(stream_response(), content_type="application/json")

        @self.app.route('/api/upload_pdf', methods=['POST'])
        def upload_pdf():
            """Route to handle PDF upload and text extraction."""
            try:
                binary_pdf = request.data
                if not binary_pdf:
                    return jsonify({"error": "No binary data received"}), 400

                text = ProcessPdf(binary_pdf)
                session['pdf_content'] = text

                return jsonify({
                    "message": "PDF text extracted successfully",
                    "content": text
                }), 200

            except Exception as e:
                return jsonify({"error": f"Failed to process the PDF: {e}"}), 500
