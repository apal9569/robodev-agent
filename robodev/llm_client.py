import json
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_MODEL = "qwen2.5:14b"
CONFIG_PATH = Path.home() / ".robodev" / "llm_config.json"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


class OllamaClient:
    def __init__(self, model: str = None, host: str = None):
        config = _load_config()
        self.default_model = model or config.get("default", DEFAULT_MODEL)
        self.task_models = config.get("tasks", {})
        self.host = (host or config.get("host", "http://localhost:11434")).rstrip("/")

    def _get_model(self, task: str = None) -> str:
        if task and task in self.task_models:
            return self.task_models[task]
        return self.default_model

    def chat(self, prompt, timeout: int = 600, task: str = None) -> str:
        model = self._get_model(task)

        # Handle both string and messages list
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        else:
            raise ValueError(f"prompt must be str or list, got {type(prompt)}")

        payload = json.dumps({
            "model": model,
            "messages": messages,
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
            print(f"🤖 Model: {model} | Task: {task or 'default'}")
            return data["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(
                f"Ollama API error {e.code} (model={model}): {error_body}"
            ) from e