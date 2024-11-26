import requests
import json


def query_ollama(prompt: str, host: str = "http://localhost:11434", model: str = "llama3.2:1b"):
    """
    Query a locally running Ollama LLaMA model.
    """
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
    }
    
    try:
        print("Sending request to Ollama...")
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()  # Raise an error for HTTP issues
            response_text = ""
            
            # Process the streamed response line by line
            for line in response.iter_lines():
                if line:  # Ignore empty lines
                    try:
                        # Parse each JSON object and extract the "response" field
                        json_obj = json.loads(line)
                        response_text += json_obj.get("response", "")
                    except json.JSONDecodeError as e:
                        print(f"JSON Decode Error: {e}")
                        continue

            return response_text

    except requests.exceptions.RequestException as e:
        return f"Error communicating with Ollama: {e}"
 
if __name__ == "__main__":
    # Example usage
    prompt = "Explain the theory of relativity in simple terms."
    response = query_ollama(prompt)
    print("\nGenerated Response:")
    print(response)
