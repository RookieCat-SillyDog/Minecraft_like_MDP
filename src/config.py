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


def load_hrm_craftworld_config() -> dict:
    return _load_yaml(MAP_DIR / "hrm_craftworld_book.yaml")


def load_pacman_delivery_config() -> dict:
    grid = _load_yaml(MAP_DIR / "pacman_delivery.yaml")["grid"]
    landmark_symbols = {
        "a": "p_a",
        "b": "p_b",
        "c": "p_c",
        "A": "d_a",
        "B": "d_b",
        "C": "d_c",
    }
    walls = []
    landmarks = {}
    for row, cells in enumerate(grid):
        for col, symbol in enumerate(cells):
            if symbol == "#":
                walls.append([row, col])
            elif symbol == "S":
                start = [row, col]
            elif symbol in landmark_symbols:
                landmarks[landmark_symbols[symbol]] = [row, col]
    return {
        "rows": len(grid),
        "cols": len(grid[0]),
        "walls": walls,
        "start": start,
        "landmarks": landmarks,
    }


def load_task_config(condition: str) -> dict:
    return _load_yaml(TASK_DIR / TASK_FILES[condition.upper()])


def load_reward_machine_config(name: str) -> dict:
    return _load_yaml(REWARD_MACHINE_DIR / f"{name}.yaml")
