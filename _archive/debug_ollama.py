import ollama
import sys
from core.config_manager import ConfigManager

try:
    cm = ConfigManager()
    host = cm.get('ollama_host', 'http://localhost:11434')
    print(f"Connecting to Ollama at: {host}")
    
    client = ollama.Client(host=host)
    resp = client.list()
    print("Raw Response:", resp)
    if hasattr(resp, 'models') and resp.models:
        first_model = resp.models[0]
        print("First Model Info:", first_model)
        # print("Keys:", first_model.__dict__.keys() if hasattr(first_model, '__dict__') else dir(first_model))
    elif isinstance(resp, dict) and resp.get('models'):
         print("First Model Info:", resp['models'][0])
    else:
        print("No models found or unknown format.")

except Exception as e:
    print(f"Error: {e}")
