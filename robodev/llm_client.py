import json
import urllib.request

class OllamaClient:
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def chat(self, messages):
        payload = json.dumps({"model": self.model, "messages": messages, "stream": False,
                                "options": {"temperature": 0.3}}).encode("utf-8")
        
        req = urllib.request.Request(f"{self.host}/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"]