"""由任务配置驱动的三因子 Minecraft MDP。"""

from collections import deque

from env.factored_tasks import (
    Action,
    AvailabilityRule,
    BEEF_FACTOR,
    DirectedTransition,
    FactoredTaskConfig,
    INDEPENDENT_TASK,
    JointState,
    KEY_FACTOR,
    LOCATION_FACTOR,
)
from env.mdp import MDP


Transition = tuple[float, JointState]


class FactoredMinecraftMDP(MDP):
    """运行 ``FactoredTaskConfig`` 描述的确定性三因子任务。

    联合状态写成 ``(location, key, beef)``。每个动作只改变一个因子，
    环境不根据任务名称或展示标签执行特殊逻辑。
    """

    def __init__(self, config: FactoredTaskConfig = INDEPENDENT_TASK):
        if not isinstance(config, FactoredTaskConfig):
            raise ValueError("config 必须是 FactoredTaskConfig")

        self.config = config

        # BFS 执行时，可达状态集合还没有建立完成。
        # 此时 _validate_state 只检查三个因子状态是否属于各自的图。
        self._state_set = None
        self._states = self._build_reachable_states()

        # BFS 完成后，环境只接受真正可达的联合状态。
        self._state_set = frozenset(self._states)

    @property
    def states(self) -> tuple[JointState, ...]:
        """返回从初始状态出发实际可达的联合状态。"""
        return self._states

    @property
    def initial_state(self) -> JointState:
        return self.config.initial_state

    @property
    def discount_factor(self) -> float:
        return self.config.discount_factor

    def actions(self, state: JointState) -> list[Action]:
        """按配置给定的固定顺序返回合法动作。"""
        self._validate_state(state)

        if self.config.is_terminal(state):
            return []

        location, key, beef = state
        legal_actions = []

        for action in self.config.action_order:
            factor = self.config.factor_for_action(action)

            if factor == LOCATION_FACTOR:
                edge = self.config.location_graph.transition(location, action)
                if edge is not None and self._rules_allow(
                    edge,
                    self.config.location_gates,
                    key,
                ):
                    legal_actions.append(action)

            elif factor == KEY_FACTOR:
                edge = self.config.key_graph.transition(key, action)
                if edge is not None:
                    legal_actions.append(action)

            elif factor == BEEF_FACTOR:
                edge = self.config.beef_graph.transition(beef, action)
                if edge is not None and self._rules_allow(
                    edge,
                    self.config.beef_gates,
                    location,
                ):
                    legal_actions.append(action)

        return legal_actions

    def transitions(
        self,
        state: JointState,
        action: Action,
    ) -> list[Transition]:
        """返回唯一的确定性转移结果。"""
        self._validate_state(state)
        self._validate_action(state, action)

        location, key, beef = state
        factor = self.config.factor_for_action(action)

        # _validate_action 已保证对应的因子图中存在这条边。
        if factor == LOCATION_FACTOR:
            edge = self.config.location_graph.transition(location, action)
            next_state = (edge.target, key, beef)
        elif factor == KEY_FACTOR:
            edge = self.config.key_graph.transition(key, action)
            next_state = (location, edge.target, beef)
        else:
            edge = self.config.beef_graph.transition(beef, action)
            next_state = (location, key, edge.target)

        return [(1.0, next_state)]

    def reward(self, state: JointState, action: Action) -> float:
        """合法动作的奖励等于对应原语代价的负数。"""
        self._validate_state(state)
        self._validate_action(state, action)
        return -self.config.action_cost(action)

    def is_terminal(self, state: JointState) -> bool:
        self._validate_state(state)
        return self.config.is_terminal(state)

    @staticmethod
    def _rules_allow(
        edge: DirectedTransition,
        rules: tuple[AvailabilityRule, ...],
        conditioning_state,
    ) -> bool:
        """若某条边受到规则控制，则所有相关规则都必须允许它。"""
        for rule in rules:
            if edge in rule.controlled_transitions:
                if not rule.allows(conditioning_state):
                    return False
        return True

    def _build_reachable_states(self) -> tuple[JointState, ...]:
        """沿实际合法转移执行 BFS，稳定地枚举可达状态。"""
        queue = deque([self.initial_state])
        visited = {self.initial_state}
        ordered_states = []

        while queue:
            state = queue.popleft()
            ordered_states.append(state)

            for action in self.actions(state):
                for probability, next_state in self.transitions(state, action):
                    if probability <= 0:
                        continue
                    if next_state not in visited:
                        visited.add(next_state)
                        queue.append(next_state)

        return tuple(ordered_states)

    def _validate_state(self, state) -> None:
        """检查状态是否属于当前环境。"""
        try:
            if self._state_set is None:
                is_valid = self._state_uses_known_factor_nodes(state)
            else:
                is_valid = state in self._state_set
        except (TypeError, IndexError):
            is_valid = False

        if not is_valid:
            raise ValueError(f"非法状态: {state}")

    def _state_uses_known_factor_nodes(self, state) -> bool:
        """BFS 建立过程中，只检查状态的三个组成部分。"""
        if not isinstance(state, tuple) or len(state) != 3:
            return False

        location, key, beef = state
        return (
            location in self.config.location_graph.nodes
            and key in self.config.key_graph.nodes
            and beef in self.config.beef_graph.nodes
        )

    def _validate_action(self, state: JointState, action: Action) -> None:
        """区分未知动作、当前不可用动作和终止状态动作。"""
        if self.config.is_terminal(state):
            raise ValueError("终止状态下不能执行动作")
        if action not in self.config.action_order:
            raise ValueError(f"未知动作: {action}")
        if action not in self.actions(state):
            raise ValueError(f"动作 {action} 在状态 {state} 下不可用")
