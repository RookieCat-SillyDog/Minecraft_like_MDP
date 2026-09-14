"""Minecraft-like Make Bridge 的确定性有限 MDP 环境。"""

from typing import List, Tuple

from env.mdp import MDP
from env.minecraft_maps import BASELINE_MAP, MinecraftMap


State = Tuple[int, int, int, int, int]
Position = Tuple[int, int]
Transition = Tuple[float, State]


class MinecraftMDP(MDP):
    """可由简单地图配置加载的 Minecraft-like Make Bridge 环境。

    状态使用 ``(row, col, wood, iron, bridge)``：
    - ``row`` 从上到下递增，``col`` 从左到右递增；
    - wood 和 iron 在进入对应资源位置时自动取得；
    - 同时持有两种资源后进入 factory，bridge 置为 1 并终止。

    每个非终止状态下的合法动作奖励均为 -1。越界动作保持原位，
    但仍然产生步长奖励。终止状态没有合法动作。
    """

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

    ACTIONS = (UP, DOWN, LEFT, RIGHT)

    ACTION_NAMES = {
        UP: "上",
        DOWN: "下",
        LEFT: "左",
        RIGHT: "右",
    }

    ACTION_DELTAS = {
        UP: (-1, 0),
        DOWN: (1, 0),
        LEFT: (0, -1),
        RIGHT: (0, 1),
    }

    STEP_REWARD = -1.0
    DISCOUNT_FACTOR = 0.95

    def __init__(self, map_config: MinecraftMap = BASELINE_MAP):
        """加载地图配置，并建立全部实际可达状态。"""
        self.map_config = map_config
        self._validate_map_config()
        self.grid_size = map_config.grid_size
        self.start = map_config.start
        self.wood = map_config.wood
        self.iron = map_config.iron
        self.factory = map_config.factory
        self.obstacles = map_config.obstacles
        self.INITIAL_STATE = (*self.start, 0, 0, 0)
        self.TERMINAL_STATE = (*self.factory, 1, 1, 1)
        self._states = self._build_states()
        self._state_set = frozenset(self._states)

    @property
    def states(self) -> Tuple[State, ...]:
        """返回从初始状态出发能够抵达的全部状态。"""
        return self._states

    @property
    def initial_state(self) -> State:
        """返回初始状态。"""
        return self.INITIAL_STATE

    @property
    def discount_factor(self) -> float:
        """返回折扣因子。"""
        return self.DISCOUNT_FACTOR

    def actions(self, state: State) -> List[int]:
        """返回当前状态下的合法动作。"""
        self._validate_state(state)

        if state == self.TERMINAL_STATE:
            return []

        return list(self.ACTIONS)

    def transitions(
        self,
        state: State,
        action: int,
    ) -> List[Transition]:
        """返回唯一的确定性转移结果。"""
        self._validate_state(state)
        self._validate_action(state, action)

        return [(1.0, self._next_state(state, action))]

    def reward(self, state: State, action: int) -> float:
        """返回当前合法动作的即时奖励。"""
        self._validate_state(state)
        self._validate_action(state, action)

        return self.STEP_REWARD

    def is_terminal(self, state: State) -> bool:
        """当 bridge 标志为 1 时返回 True。"""
        self._validate_state(state)
        return state[4] == 1

    def _next_state(self, state: State, action: int) -> State:
        """按照移动、收集、合成的顺序计算下一状态。"""
        row, col, has_wood, has_iron, has_bridge = state
        row_change, col_change = self.ACTION_DELTAS[action]

        new_row = row + row_change
        new_col = col + col_change

        # 越界或撞到障碍时留在原位。
        if (
            self._is_inside_grid(new_row, new_col)
            and (new_row, new_col) not in self.obstacles
        ):
            next_position = (new_row, new_col)
        else:
            next_position = (row, col)

        # 进入资源格时自动收集；已经收集的资源不会丢失
        if next_position == self.wood:
            has_wood = 1
        if next_position == self.iron:
            has_iron = 1

        # 两种资源齐全后进入 factory，立即完成 bridge
        if next_position == self.factory and has_wood and has_iron:
            has_bridge = 1

        next_row, next_col = next_position
        return (next_row, next_col, has_wood, has_iron, has_bridge)

    def _build_states(self) -> Tuple[State, ...]:
        """根据资源规则建立全部实际可达状态。"""
        states = []

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                position = (row, col)

                if position in self.obstacles:
                    continue

                # 未取得资源时，不能站在资源格上。
                if position not in (self.wood, self.iron):
                    states.append((row, col, 0, 0, 0))

                # 只取得 wood 时，不能站在 iron 格上。
                if position != self.iron:
                    states.append((row, col, 1, 0, 0))

                # 只取得 iron 时，不能站在 wood 格上。
                if position != self.wood:
                    states.append((row, col, 0, 1, 0))

                # 两种资源齐全时，进入 factory 会立即终止。
                if position != self.factory:
                    states.append((row, col, 1, 1, 0))

        states.append(self.TERMINAL_STATE)
        return tuple(states)

    def _is_inside_grid(self, row: int, col: int) -> bool:
        """判断位置是否位于地图内。"""
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

    def _validate_map_config(self) -> None:
        """检查会使地图规则无法成立的常见布局错误。"""
        if not isinstance(self.map_config, MinecraftMap):
            raise ValueError("map_config 必须是 MinecraftMap")
        if self.map_config.grid_size <= 0:
            raise ValueError("grid_size 必须大于 0")

        positions = {
            "start": self.map_config.start,
            "wood": self.map_config.wood,
            "iron": self.map_config.iron,
            "factory": self.map_config.factory,
        }
        for name, position in positions.items():
            if not self._position_is_inside_map(position):
                raise ValueError(f"{name} 超出地图范围: {position}")

        if len(set(positions.values())) != len(positions):
            raise ValueError("start、wood、iron 和 factory 不能重合")

        for obstacle in self.map_config.obstacles:
            if not self._position_is_inside_map(obstacle):
                raise ValueError(f"障碍超出地图范围: {obstacle}")
            if obstacle in positions.values():
                raise ValueError(f"障碍不能覆盖关键位置: {obstacle}")

    def _position_is_inside_map(self, position: Position) -> bool:
        """在地图配置校验时判断一个坐标是否在范围内。"""
        row, col = position
        return (
            isinstance(row, int)
            and isinstance(col, int)
            and 0 <= row < self.map_config.grid_size
            and 0 <= col < self.map_config.grid_size
        )

    def _validate_state(self, state: State) -> None:
        """检查状态是否属于实际可达状态空间。"""
        try:
            is_valid = state in self._state_set
        except TypeError as error:
            raise ValueError(f"非法状态: {state}") from error

        if not is_valid:
            raise ValueError(f"非法状态: {state}")

    def _validate_action(self, state: State, action: int) -> None:
        """检查动作在当前状态下是否合法。"""
        if state[4] == 1:
            raise ValueError("终止状态下不能执行动作")

        if action not in self.ACTIONS:
            raise ValueError(f"非法动作: {action}")

    def render(self) -> str:
        """返回当前地图的字符串表示。"""
        lines = [
            f"Minecraft-like Make Bridge {self.grid_size}x{self.grid_size}",
            "=" * (self.grid_size * 4 + 1),
        ]

        for row in range(self.grid_size):
            symbols = []

            for col in range(self.grid_size):
                position = (row, col)

                if position == self.start:
                    symbols.append(" S ")
                elif position in self.obstacles:
                    symbols.append(" X ")
                elif position == self.wood:
                    symbols.append(" W ")
                elif position == self.iron:
                    symbols.append(" I ")
                elif position == self.factory:
                    symbols.append(" F ")
                else:
                    symbols.append(" . ")

            lines.append("|" + "|".join(symbols) + "|")

        lines.append("=" * (self.grid_size * 4 + 1))
        lines.append("S: 起点, W: wood, I: iron, F: factory, X: 障碍, .: 可通行")

        return "\n".join(lines)
