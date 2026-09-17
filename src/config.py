from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
MAP_DIR = REPOSITORY_ROOT / "configs" / "maps"
TASK_DIR = REPOSITORY_ROOT / "configs" / "tasks"
REWARD_MACHINE_DIR = REPOSITORY_ROOT / "configs" / "reward_machines"
TASK_FILES = {
    "A": "task_01.yaml",
    "B": "task_02.yaml",
}


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_map_config() -> dict:
    return _load_yaml(MAP_DIR / "map_01.yaml")


def load_officeworld_config() -> dict:
    return _load_yaml(MAP_DIR / "officeworld_minimal.yaml")


def load_task_config(condition: str) -> dict:
    return _load_yaml(TASK_DIR / TASK_FILES[condition.upper()])


def load_reward_machine_config(name: str) -> dict:
    return _load_yaml(REWARD_MACHINE_DIR / f"{name}.yaml")
