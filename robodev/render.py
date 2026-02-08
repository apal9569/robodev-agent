from pathlib import Path
from typing import List

def render_brainstorm(text: str) -> str:
    return text.strip()

def render_codegen(text: str, files: List[Path]) -> str:
    lines = [text.strip(), ""]
    if files:
        lines.append("Wrote files:")
        for f in files:
            lines.append(f" - {f}")
    else:
        lines.append("No files were written.")
    return "\n".join(lines)

def render_diagnose(text: str) -> str:
    return text.strip()