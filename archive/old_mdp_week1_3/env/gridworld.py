"""确定性 5x5 GridWorld 环境。"""

from typing import List, Tuple

from env.mdp import MDP


State = Tuple[int, int]
Transition = Tuple[float, State]


class GridWorld(MDP):
    """固定的确定性 5x5 GridWorld。

    坐标使用 (row, col)：
    - row 从上到下递增
    - col 从左到右递增

    每个非终止状态下的合法动作奖励均为 -1。
    终止状态没有合法动作，其价值由算法定义为 0。
    """

    # 固定地图配置
    grid_size = 5
    start: State = (0, 0)
    goal: State = (4, 4)
    obstacles = frozenset({
        (1, 1),
        (2, 2),
        (3, 1),
    })

    # 动作编号
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

    # 每个动作对行、列造成的变化
    ACTION_DELTAS = {
        UP: (-1, 0),
        DOWN: (1, 0),
        LEFT: (0, -1),
        RIGHT: (0, 1),
    }

    STEP_REWARD = -1.0
    DISCOUNT_FACTOR = 0.9

    def __init__(self):
        """建立固定地图的状态空间。"""
        self._states = tuple(
            (row, col)
            for row in range(self.grid_size)
            for col in range(self.grid_size)
            if (row, col) not in self.obstacles
        )

        # 集合适合快速判断一个状态是否合法
        self._state_set = frozenset(self._states)

    @property
    def states(self) -> Tuple[State, ...]:
        """返回全部合法状态。"""
        return self._states

    @property
    def initial_state(self) -> State:
        """返回初始状态。"""
        return self.start

    @property
    def discount_factor(self) -> float:
        """返回折扣因子。"""
        return self.DISCOUNT_FACTOR

    def actions(self, state: State) -> List[int]:
        """返回当前状态下的合法动作。"""
        self._validate_state(state)

        if state == self.goal:
            return []

        return list(self.ACTIONS)

    def transitions(
        self,
        state: State,
        action: int,
    ) -> List[Transition]:
        """返回确定性转移结果。"""
        self._validate_state(state)
        self._validate_action(state, action)

        row, col = state
        row_change, col_change = self.ACTION_DELTAS[action]

        candidate = (
            row + row_change,
            col + col_change,
        )

        # 越界位置和障碍位置都不在合法状态集合中
        if candidate not in self._state_set:
            next_state = state
        else:
            next_state = candidate

        return [(1.0, next_state)]

    def reward(self, state: State, action: int) -> float:
        """返回当前合法动作的即时奖励。"""
        self._validate_state(state)
        self._validate_action(state, action)

        return self.STEP_REWARD

    def is_terminal(self, state: State) -> bool:
        """判断状态是否为终止状态。"""
        self._validate_state(state)
        return state == self.goal

    def _validate_state(self, state: State) -> None:
        """检查状态是否属于状态空间。"""
        if state not in self._state_set:
            raise ValueError(f"非法状态: {state}")

    def _validate_action(self, state: State, action: int) -> None:
        """检查动作在当前状态下是否合法。"""
        if state == self.goal:
            raise ValueError("终止状态下不能执行动作")

        if action not in self.ACTIONS:
            raise ValueError(f"非法动作: {action}")

    def render(self) -> str:
        """返回地图的字符串表示。"""
        lines = [
            f"GridWorld {self.grid_size}x{self.grid_size}",
            "=" * (self.grid_size * 4 + 1),
        ]

        for row in range(self.grid_size):
            symbols = []

            for col in range(self.grid_size):
                position = (row, col)

                if position == self.start:
                    symbols.append(" S ")
                elif position == self.goal:
                    symbols.append(" G ")
                elif position in self.obstacles:
                    symbols.append(" X ")
                else:
                    symbols.append(" . ")

            lines.append("|" + "|".join(symbols) + "|")

        lines.append("=" * (self.grid_size * 4 + 1))
        lines.append("S: 起点, G: 终点, X: 障碍物, .: 可通行")

        return "\n".join(lines)