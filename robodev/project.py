from pathlib import Path

IGNORED_DIRS = [".git", "__pycache__", "build", "dist", "install", "logs"]

def list_project_tree(root, max_depth=5):
    root = Path(root)
    out = []

    def walk(path, depth):
        if depth > max_depth:
            return
        for child in sorted(path.iterdir()):
            if child.name in IGNORED_DIRS:
                continue
            out.append(" " * depth + child.name)
            if child.is_dir():
                walk(child, depth + 1)


    walk(root, 0)
    return '\n'.join(out)

def read_project_file(root, rel_path, max_chars = 10000):
    p = Path(root) / rel_path
    if not p.exists() or not p.is_file():
        return FileNotFoundError(f"File not found: {rel_path}")
    text = p.read_text(encoding="utf-8", errors="ignore")
    return text[:max_chars]