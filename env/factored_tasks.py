"""三因子 Minecraft 的基础图和任务配置。

这里只描述“任务是什么”；联合状态转移和 BFS 由
``factored_minecraft.py`` 实现。阅读顺序是：状态与动作、通用数据结构、
三张因子图，最后是 ``INDEPENDENT_TASK``。
"""

from dataclasses import dataclass
from typing import Callable, Mapping


# 1. 状态、因子和动作

Action = str
FactorName = str
FactorState = tuple[int, int]

LocationState = FactorState
KeyState = FactorState
BeefState = FactorState
ContextState = tuple[KeyState, BeefState]
JointState = tuple[LocationState, KeyState, BeefState]
LocationEdge = frozenset[LocationState]

LOCATION_FACTOR = "L"
KEY_FACTOR = "K"
BEEF_FACTOR = "B"
FACTOR_ORDER = (LOCATION_FACTOR, KEY_FACTOR, BEEF_FACTOR)

UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"

HEAD_BLACK = "head-black"
HEAD_WHITE = "head-white"
TAIL_BLACK = "tail-black"
TAIL_WHITE = "tail-white"

HEAT = "heat"
COOL = "cool"
CHOP = "chop"
STIR = "stir"

LOCATION_ACTIONS = (UP, DOWN, LEFT, RIGHT)
KEY_ACTIONS = (HEAD_BLACK, HEAD_WHITE, TAIL_BLACK, TAIL_WHITE)
BEEF_ACTIONS = (HEAT, COOL, CHOP, STIR)
ACTION_ORDER = LOCATION_ACTIONS + KEY_ACTIONS + BEEF_ACTIONS


def context_of(state: JointState) -> ContextState:
    """从 ``(location, key, beef)`` 中取出 ``(key, beef)``。"""
    return state[1], state[2]


# 2. 通用数据结构

@dataclass(frozen=True)
class DirectedTransition:
    """因子图中的一条有向边：source --action--> target。"""

    source: FactorState
    action: Action
    target: FactorState


@dataclass
class FactorGraph:
    """保存一个因子的节点、动作、有向边和绘图信息。"""

    name: FactorName
    nodes: tuple[FactorState, ...]
    actions: tuple[Action, ...]
    transitions: tuple[DirectedTransition, ...]
    labels: Mapping[FactorState, str]
    coordinates: Mapping[FactorState, tuple[float, float]]

    def __post_init__(self) -> None:
        """dataclass 创建对象后会自动执行这里。"""
        self.nodes = tuple(self.nodes)
        self.actions = tuple(self.actions)
        self.transitions = tuple(self.transitions)
        self.labels = dict(self.labels)
        self.coordinates = dict(self.coordinates)

        if not self.name or not self.nodes or not self.actions:
            raise ValueError("factor graph 的 name、nodes 和 actions 不能为空")
        if len(self.nodes) != len(set(self.nodes)) or len(self.actions) != len(
            set(self.actions)
        ):
            raise ValueError(f"{self.name} 的 nodes 或 actions 有重复")
        if set(self.labels) != set(self.nodes) or set(self.coordinates) != set(
            self.nodes
        ):
            raise ValueError(f"{self.name} 的每个节点都需要 label 和 coordinate")

        state_actions = []
        for edge in self.transitions:
            if (
                edge.source not in self.nodes
                or edge.target not in self.nodes
                or edge.action not in self.actions
                or edge.source == edge.target
            ):
                raise ValueError(f"{self.name} 含有非法 transition: {edge}")
            state_actions.append((edge.source, edge.action))
        if len(state_actions) != len(set(state_actions)):
            raise ValueError(f"{self.name} 的同一状态和动作不能有两个结果")

    def outgoing(self, state: FactorState) -> tuple[DirectedTransition, ...]:
        """返回从 ``state`` 出发的全部有向边。"""
        if state not in self.nodes:
            raise ValueError(f"{self.name} 中不存在状态 {state}")

        result = []
        for edge in self.transitions:
            if edge.source == state:
                result.append(edge)
        return tuple(result)

    def transition(
        self,
        state: FactorState,
        action: Action,
    ) -> DirectedTransition | None:
        """返回指定的边；动作不可用时返回 ``None``。"""
        for edge in self.outgoing(state):
            if edge.action == action:
                return edge
        return None

    def has_connection(self, source: FactorState, target: FactorState) -> bool:
        """判断图中是否存在 ``source -> target`` 的边。"""
        for edge in self.outgoing(source):
            if edge.target == target:
                return True
        return False


@dataclass
class AvailabilityRule:
    """条件因子处于允许状态时，开放目标因子的指定转移。"""

    name: str
    conditioning_factor: FactorName
    target_factor: FactorName
    controlled_transitions: tuple[DirectedTransition, ...]
    allowed_condition_states: frozenset[FactorState]

    def __post_init__(self) -> None:
        self.controlled_transitions = tuple(self.controlled_transitions)
        self.allowed_condition_states = frozenset(self.allowed_condition_states)

        if not self.name or not self.controlled_transitions:
            raise ValueError("availability rule 缺少 name 或 transition")
        if not self.allowed_condition_states:
            raise ValueError("allowed_condition_states 不能为空")
        if len(self.controlled_transitions) != len(
            set(self.controlled_transitions)
        ):
            raise ValueError("availability rule 中有重复 transition")

    def allows(self, conditioning_state: FactorState) -> bool:
        return conditioning_state in self.allowed_condition_states


@dataclass(frozen=True)
class ExactTerminalPredicate:
    """仅当联合状态等于 ``goal_state`` 时终止。"""

    goal_state: JointState

    def __call__(self, state: JointState) -> bool:
        return state == self.goal_state


@dataclass
class FactoredTaskConfig:
    """运行一个三因子任务所需的全部配置。"""

    task_name: str
    location_graph: FactorGraph
    key_graph: FactorGraph
    beef_graph: FactorGraph
    blocked_location_edges: frozenset[LocationEdge]
    location_landmarks: Mapping[str, LocationState]
    edge_landmarks: Mapping[str, LocationEdge]
    location_gates: tuple[AvailabilityRule, ...]
    beef_gates: tuple[AvailabilityRule, ...]
    initial_state: JointState
    terminal_predicate: Callable[[JointState], bool]
    primitive_costs: Mapping[Action, float]
    action_order: tuple[Action, ...]
    discount_factor: float = 0.95

    def __post_init__(self) -> None:
        """统一容器类型，再检查配置之间是否一致。"""
        self.blocked_location_edges = frozenset(self.blocked_location_edges)
        self.location_landmarks = dict(self.location_landmarks)
        self.edge_landmarks = dict(self.edge_landmarks)
        self.location_gates = tuple(self.location_gates)
        self.beef_gates = tuple(self.beef_gates)
        self.primitive_costs = dict(self.primitive_costs)
        self.action_order = tuple(self.action_order)
        self.validate()

    @property
    def graphs(self) -> tuple[FactorGraph, FactorGraph, FactorGraph]:
        return self.location_graph, self.key_graph, self.beef_graph

    @property
    def coupling_rules(self) -> tuple[AvailabilityRule, ...]:
        return self.location_gates + self.beef_gates

    def graph_for(self, factor: FactorName) -> FactorGraph:
        if factor == LOCATION_FACTOR:
            return self.location_graph
        if factor == KEY_FACTOR:
            return self.key_graph
        if factor == BEEF_FACTOR:
            return self.beef_graph
        raise ValueError(f"未知 factor: {factor}")

    def factor_for_action(self, action: Action) -> FactorName:
        if action in self.location_graph.actions:
            return LOCATION_FACTOR
        if action in self.key_graph.actions:
            return KEY_FACTOR
        if action in self.beef_graph.actions:
            return BEEF_FACTOR
        raise ValueError(f"未知 action: {action}")

    def action_cost(self, action: Action) -> float:
        if action not in self.primitive_costs:
            raise ValueError(f"未知 action: {action}")
        return self.primitive_costs[action]

    def is_terminal(self, state: JointState) -> bool:
        return bool(self.terminal_predicate(state))

    def validate(self) -> None:
        """只检查会使通用环境无法运行的配置错误。"""
        if not self.task_name:
            raise ValueError("task_name 不能为空")
        if tuple(graph.name for graph in self.graphs) != FACTOR_ORDER:
            raise ValueError("三张图的 name 必须依次为 L、K、B")

        all_actions = tuple(
            action for graph in self.graphs for action in graph.actions
        )
        if (
            len(all_actions) != len(set(all_actions))
            or len(self.action_order) != len(set(self.action_order))
            or set(self.action_order) != set(all_actions)
            or set(self.primitive_costs) != set(all_actions)
        ):
            raise ValueError("动作必须全局唯一，并被顺序和代价完整覆盖")
        if any(cost <= 0 for cost in self.primitive_costs.values()):
            raise ValueError("primitive cost 必须大于 0")
        if not 0 <= self.discount_factor < 1:
            raise ValueError("discount_factor 必须位于 [0, 1)")
        if len(self.initial_state) != 3 or any(
            state not in graph.nodes
            for state, graph in zip(self.initial_state, self.graphs)
        ):
            raise ValueError("initial_state 中有状态不属于对应因子图")
        if not callable(self.terminal_predicate):
            raise ValueError("terminal_predicate 必须可调用")
        if self.is_terminal(self.initial_state):
            raise ValueError("initial_state 不能已经终止")

        rule_groups = (
            (self.location_gates, self.key_graph, self.location_graph),
            (self.beef_gates, self.location_graph, self.beef_graph),
        )
        for rules, condition_graph, target_graph in rule_groups:
            for rule in rules:
                if rule.conditioning_factor != condition_graph.name:
                    raise ValueError(f"{rule.name} 的 conditioning factor 不正确")
                if rule.target_factor != target_graph.name:
                    raise ValueError(f"{rule.name} 的 target factor 不正确")
                if not rule.allowed_condition_states.issubset(
                    condition_graph.nodes
                ):
                    raise ValueError(f"{rule.name} 含有不存在的条件状态")
                if not set(rule.controlled_transitions).issubset(
                    target_graph.transitions
                ):
                    raise ValueError(f"{rule.name} 引用了不存在的 transition")


def make_undirected_edge(
    first: LocationState,
    second: LocationState,
) -> LocationEdge:
    """用两个端点建立一条无向边。"""
    edge = frozenset((first, second))
    if len(edge) != 2:
        raise ValueError("一条边必须连接两个不同节点")
    return edge


# 3. 三张 3x3 因子图

LOCATION_STATES = tuple((row, col) for row in range(3) for col in range(3))
KEY_STATES = tuple((head, tail) for head in range(3) for tail in range(3))
BEEF_STATES = tuple(
    (cooking, processing)
    for cooking in range(3)
    for processing in range(3)
)

START_LOCATION = (2, 0)
GOAL_LOCATION = (2, 2)
BOARD_LOCATION = (1, 1)
KITCHEN_LOCATION = (1, 2)

WALLS = frozenset(
    {
        make_undirected_edge((0, 1), (0, 2)),
        make_undirected_edge((2, 1), (2, 2)),
    }
)
DOOR_EDGE = make_undirected_edge(BOARD_LOCATION, KITCHEN_LOCATION)

ACTION_DELTAS = {
    UP: (-1, 0),
    DOWN: (1, 0),
    LEFT: (0, -1),
    RIGHT: (0, 1),
}


def _location_transitions() -> tuple[DirectedTransition, ...]:
    """建立 Location 网格中的合法移动边。"""
    transitions = []
    for source in LOCATION_STATES:
        for action, (row_change, col_change) in ACTION_DELTAS.items():
            target = (source[0] + row_change, source[1] + col_change)
            if (
                target in LOCATION_STATES
                and make_undirected_edge(source, target) not in WALLS
            ):
                transitions.append(DirectedTransition(source, action, target))
    return tuple(transitions)


def _key_transitions() -> tuple[DirectedTransition, ...]:
    """建立 Key 的 head 和 tail 属性变换边。"""
    transitions = []
    for head, tail in KEY_STATES:
        source = (head, tail)
        possible_results = {
            HEAD_BLACK: (1, tail),
            HEAD_WHITE: (2, tail),
            TAIL_BLACK: (head, 1),
            TAIL_WHITE: (head, 2),
        }
        for action, target in possible_results.items():
            if target != source:
                transitions.append(DirectedTransition(source, action, target))
    return tuple(transitions)


def _beef_transitions() -> tuple[DirectedTransition, ...]:
    """建立 Beef 的 cooking 和 processing 变换边。"""
    transitions = []
    for cooking, processing in BEEF_STATES:
        source = (cooking, processing)
        if cooking < 2:
            transitions.append(
                DirectedTransition(source, HEAT, (cooking + 1, processing))
            )
        if cooking > 0:
            transitions.append(
                DirectedTransition(source, COOL, (cooking - 1, processing))
            )
        if processing == 0:
            transitions.append(DirectedTransition(source, CHOP, (cooking, 1)))
        if processing == 1:
            transitions.append(DirectedTransition(source, STIR, (cooking, 2)))
    return tuple(transitions)


KEY_LEVEL_LABELS = {0: "blank", 1: "black", 2: "white"}
COOKING_LABELS = {0: "raw", 1: "medium", 2: "cooked"}
PROCESSING_LABELS = {0: "whole", 1: "sliced", 2: "minced"}


LOCATION_GRAPH = FactorGraph(
    name=LOCATION_FACTOR,
    nodes=LOCATION_STATES,
    actions=LOCATION_ACTIONS,
    transitions=_location_transitions(),
    labels={state: str(state) for state in LOCATION_STATES},
    # 状态是 (row, col)，绘图坐标是 (x, y)=(col, row)。
    coordinates={state: (state[1], state[0]) for state in LOCATION_STATES},
)

KEY_GRAPH = FactorGraph(
    name=KEY_FACTOR,
    nodes=KEY_STATES,
    actions=KEY_ACTIONS,
    transitions=_key_transitions(),
    labels={
        state: f"{KEY_LEVEL_LABELS[state[0]]}/{KEY_LEVEL_LABELS[state[1]]}"
        for state in KEY_STATES
    },
    coordinates={state: state for state in KEY_STATES},
)

BEEF_GRAPH = FactorGraph(
    name=BEEF_FACTOR,
    nodes=BEEF_STATES,
    actions=BEEF_ACTIONS,
    transitions=_beef_transitions(),
    labels={
        state: (
            f"{COOKING_LABELS[state[0]]}/{PROCESSING_LABELS[state[1]]}"
        )
        for state in BEEF_STATES
    },
    coordinates={state: state for state in BEEF_STATES},
)


# 4. Day 11–12：independent anchor

INITIAL_STATE: JointState = (START_LOCATION, (0, 0), (0, 0))
GOAL_STATE: JointState = (GOAL_LOCATION, (2, 2), (2, 2))

PRIMITIVE_COSTS = {action: 1.0 for action in ACTION_ORDER}

# independent 中，门和功能区只是地图标记，不限制动作。
INDEPENDENT_TASK = FactoredTaskConfig(
    task_name="independent",
    location_graph=LOCATION_GRAPH,
    key_graph=KEY_GRAPH,
    beef_graph=BEEF_GRAPH,
    blocked_location_edges=WALLS,
    location_landmarks={
        "start": START_LOCATION,
        "goal": GOAL_LOCATION,
        "board": BOARD_LOCATION,
        "kitchen": KITCHEN_LOCATION,
    },
    edge_landmarks={"door": DOOR_EDGE},
    location_gates=(),
    beef_gates=(),
    initial_state=INITIAL_STATE,
    terminal_predicate=ExactTerminalPredicate(GOAL_STATE),
    primitive_costs=PRIMITIVE_COSTS,
    action_order=ACTION_ORDER,
)

TASK_CONFIGS = {"independent": INDEPENDENT_TASK}


def get_task_config(task_name: str) -> FactoredTaskConfig:
    """按名称取得任务配置。"""
    if task_name not in TASK_CONFIGS:
        raise ValueError(f"未知 factored task: {task_name}")
    return TASK_CONFIGS[task_name]
