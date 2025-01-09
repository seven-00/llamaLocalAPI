import json
import requests


class QueryOllama:
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2:1b"):
        """Initialize with default API host and model."""
        self.host = host
        self.model = model

    def query_stream(self, prompt: str):
        """Stream the response from Ollama API and yield JSON chunks as they arrive."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
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
                            print("Failed to decode JSON from chunk")
                            continue
        except requests.exceptions.RequestException as e:
            yield {"error": f"Error communicating with Ollama: {e}"}
