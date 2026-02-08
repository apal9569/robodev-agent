import json
from pathlib import Path

DEFAULT = {
    "project_root": None,
    "model": "llama3.1",
    "stack": "ROS2",
    "sim": "Gazebo",
    "language": "Python",
    "robot_type": "drone",
    "style": "concise"
}

class AgentMemory:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def path() -> Path:
        return Path.home() / ".robodev_memory.json"
    
    @classmethod
    def load(cls):
        p = cls.path()
        if p.exists():
            return cls(json.loads(p.read_text()))
        return cls(DEFAULT.copy())
    
    def save(self):
        self.path().write_text(json.dumps(self.data, indent=2))

    def pretty(self) -> str:
        lines = ["RoboDev config:"]
        for key, value in self.data.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)