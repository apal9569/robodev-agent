import re 
from pathlib import Path
from typing import List

FILE_RE = re.compile(r"# filename:\s*(.+)\n```[^\n]*\n(.*?)\n```", re.DOTALL)

def write_artifacts(llm_text: str,  out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fnames, content in FILE_RE.findall(llm_text):
        file_path = out_dir / fnames.strip()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        written.append(file_path)
    return written