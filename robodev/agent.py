from pathlib import Path
from robodev.llm_client import OllamaClient
from robodev.prompts import (
    system_prompt,
    brainstorm_prompt,
    codegen_prompt,
    diagnose_prompt
)
from robodev.artifacts import write_artifacts
from robodev.render import render_brainstorm, render_codegen, render_diagnose
from robodev.project import list_project_tree
import shlex

class RoboDevAgent:
    def __init__(self, memory):
        self.memory = memory
        self.llm = OllamaClient()
        
    def brainstorm(self, query: str) -> str:
        msgs = [
            {"role": "system", "content": system_prompt(self.memory)},
            {"role": "user", "content": brainstorm_prompt(self.memory, query=query)}
        ]
        resp = self.llm.chat(msgs, task="brainstorm")
        return render_brainstorm(resp)
    
    def codegen(self, query: str, lang: str = "python", xml: str = None, out_dir: Path = Path("./generated")) -> str:
        msgs = [
            {"role": "system", "content": system_prompt(self.memory)},
            {"role": "user", "content": codegen_prompt(self.memory, query=query, lang=lang, xml=xml)}
        ]
        resp = self.llm.chat(msgs, task="codegen")
        files = write_artifacts(resp, out_dir)
        return render_codegen(resp, files)
    
    def diagnose(self, log_text: str) -> str:
        msgs = [
            {"role": "system", "content": system_prompt(self.memory)},
            {"role": "user", "content": diagnose_prompt(self.memory, log_text=log_text)}
        ]
        resp = self.llm.chat(msgs, task="diagnose")
        return render_diagnose(resp)
    
    def interactive(self):
        mode = self.memory.data.get("default_mode", "brainstorm")
        prompt = f"RoboDev Interactive Mode (model = {self.memory.data.get('model')}, stack = {self.memory.data.get('stack')})> "

        print("Type: brainstorm|codegen|diagnose <text> | /mode <name> | /config | /exit")
        print("Shortcuts: b <text> | c <text> | d <text>")

        while True:
            try:
                line = input(f"robodev[{mode}]> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSee yaa")
                return
            
            if not line:
                continue
            
            if line.startswith("/exit") or line.startswith("/quit"):
                print("Exiting interactive mode.")
                return
            
            if line.startswith("/mode"):
                parts = line.split(maxsplit=1)
                if len(parts) == 2 and parts[1] in ["brainstorm", "codegen", "diagnose"]:
                    mode = parts[1]
                    self.memory.data["default_mode"] = mode
                    self.memory.save()
                else:
                    print("Invalid mode. Available modes: brainstorm, codegen, diagnose.")
                    continue

            if line == "/config":
                print(self.memory.pretty())
                continue
            if line.startswith("/set "):
                kvs = shlex.split(line[len("/set "):])
                for kv in kvs:
                    if "=" in kv:
                        key, value = kv.split("=", 1)
                        self.memory.data[key] = value
                self.memory.save()
                continue

            if line.startswith("/project"):
                parts = line.split(maxsplit=2)
                if len(parts) == 1 or parts[1] == "show":
                    root = self.memory.data.get("project_root")
                    if root:
                        print(f"Project root: {root}")
                    else:
                        print("Project root is not set.")
                elif parts[1] == "set" and len(parts) == 3:
                    p = Path(parts[2]).expanduser().resolve()
                    if not p.exists() or not p.is_dir():
                        print(f"Invalid path: {p}")
                    else:
                        self.memory.data["project_root"] = str(p)
                        self.memory.save()
                        print(f"Project root set to: {p}")
                    continue
                print("Usage: /project show | /project set <path>")

            if line == "/project tree":
                root = self.memory.data.get("project_root")
                if not root:
                    print("Project root is not set.")
                else:
                    print(list_project_tree(root))
                continue

            if line.startswith("b "):
                cmd, rest = "brainstorm", line[2:]
            elif line.startswith("c "):
                cmd, rest = "codegen", line[2:]
            elif line.startswith("d "):
                cmd, rest = "diagnose", line[2:]
            else:
                parts = line.split(maxsplit=1)
                if parts[0] in ["brainstorm", "codegen", "diagnose"]:
                    cmd = parts[0]
                    rest = parts[1] if len(parts) > 1 else ""
                else:
                    cmd, rest = mode, line
            
            if cmd == "brainstorm":
                print(self.brainstorm(rest))
            elif cmd == "codegen":
                out_dir = Path(self.memory.data.get("out_dir", "./generated"))
                lang = self.memory.data.get("language", "python")
                xml = self.memory.data.get("xml", None)
                print(self.codegen(rest, lang=lang, xml=xml, out_dir=out_dir))
            elif cmd == "diagnose":
                if rest.endswith(".log") or rest.endswith(".txt"):
                    p = Path(rest)
                    if p.exists():
                        print(self.diagnose(p.read_text(encoding="utf-8", errors="ignore")))
                    else:
                        print(f"File not found: {rest}")
                else:
                    print(self.diagnose(rest))