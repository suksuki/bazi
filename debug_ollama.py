import ollama
import sys

try:
    # Try localhost first as a baseline
    client = ollama.Client(host='http://localhost:11434')
    resp = client.list()
    print("Raw Response:", resp)
    print("Keys in first model:", resp['models'][0].keys() if resp.get('models') else "No models")
except Exception as e:
    print(f"Error: {e}")
