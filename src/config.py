from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
MAP_DIR = REPOSITORY_ROOT / "configs" / "maps"
TASK_DIR = REPOSITORY_ROOT / "configs" / "tasks"
TASK_FILES = {
    "A": "task_01.yaml",
    "B": "task_02.yaml",
}


def load_map_config() -> dict:
    path = MAP_DIR / "map_01.yaml"
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_task_config(condition: str) -> dict:
    path = TASK_DIR / TASK_FILES[condition.upper()]
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)
