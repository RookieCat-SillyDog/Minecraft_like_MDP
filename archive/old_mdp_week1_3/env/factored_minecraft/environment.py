"""三因子 MDP 的通用执行器。"""

from collections import deque

from env.factored_minecraft.maps import Action, FactorState, JointState, MapConfig
from env.mdp import MDP


Edge = tuple[FactorState, Action, FactorState]
Transition = tuple[float, JointState]


def successors(
    map_config: MapConfig,
    state: JointState,
    rules=(),
) -> list[tuple[Action, JointState]]:
    """返回按地图动作规格排列的合法后继，不要求 state 可达。"""
    if state in map_config.terminal_states:
        return []

    result = []
    for action, factor in map_config.action_spec:
        target = map_config.factor_moves[factor].get((state[factor], action))
        if target is None:
            continue

        edge = (state[factor], action, target)
        if any(not rule(map_config, state, edge) for rule in rules):
            continue

        next_state = list(state)
        next_state[factor] = target
        result.append((action, tuple(next_state)))

    return result


class FactoredMinecraftMDP(MDP):
    """运行指定地图和规则的确定性三因子任务。"""

    def __init__(self, map_config: MapConfig, rules=()):
        self.map_config = map_config
        self.rules = rules
        self.moves = map_config.factor_moves
        self.action_factor = dict(map_config.action_spec)
        self._successors = {}
        self._states = self._build_reachable_states()

    @property
    def states(self) -> tuple[JointState, ...]:
        return self._states

    @property
    def initial_state(self) -> JointState:
        return self.map_config.initial_state

    @property
    def terminal_states(self) -> frozenset[JointState]:
        return self.map_config.terminal_states

    @property
    def discount_factor(self) -> float:
        return self.map_config.discount_factor

    def actions(self, state: JointState) -> list[Action]:
        return list(self._successors[state])

    def transitions(self, state: JointState, action: Action) -> list[Transition]:
        return [(1.0, self._successors[state][action])]

    def reward(self, state: JointState, action: Action) -> float:
        self.transitions(state, action)
        return -1.0

    def is_terminal(self, state: JointState) -> bool:
        return state in self.terminal_states

    def _build_reachable_states(self) -> tuple[JointState, ...]:
        queue = deque([self.initial_state])
        self._successors[self.initial_state] = dict(
            successors(self.map_config, self.initial_state, self.rules)
        )
        ordered_states = []

        while queue:
            state = queue.popleft()
            ordered_states.append(state)

            for next_state in self._successors[state].values():
                if next_state not in self._successors:
                    self._successors[next_state] = dict(
                        successors(self.map_config, next_state, self.rules)
                    )
                    queue.append(next_state)

        return tuple(ordered_states)
