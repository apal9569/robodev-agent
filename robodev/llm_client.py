import json
import urllib.request

class OllamaClient:
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def chat(self, prompt: str, timeout: int = 300) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return data["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(
                f"Ollama API error {e.code}: {error_body}"
            ) from e