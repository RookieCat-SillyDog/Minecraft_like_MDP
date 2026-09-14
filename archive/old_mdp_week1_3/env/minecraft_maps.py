"""Minecraft-like 环境使用的两张小型地图配置。"""

from dataclasses import dataclass
from typing import FrozenSet, Tuple


Position = Tuple[int, int]


@dataclass(frozen=True)
class MinecraftMap:
    """只描述地图布局，不包含奖励或算法参数。"""

    name: str
    grid_size: int
    start: Position
    wood: Position
    iron: Position
    factory: Position
    obstacles: FrozenSet[Position]


BASELINE_MAP = MinecraftMap(
    name="baseline",
    grid_size=5,
    start=(0, 0),
    wood=(0, 4),
    iron=(4, 0),
    factory=(4, 4),
    obstacles=frozenset(),
)


CHALLENGE_MAP = MinecraftMap(
    name="challenge",
    grid_size=5,
    start=(0, 0),
    wood=(0, 4),
    iron=(4, 0),
    factory=(0, 2),
    obstacles=frozenset({(1, 0)}),
)
