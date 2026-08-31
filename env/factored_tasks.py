"""定义三因子 Minecraft 的基础图、可用性规则和 task anchors。"""

from dataclasses import dataclass, field, replace
from typing import Callable, Mapping


# 1. 状态、因子和动作

Action = str
FactorName = str
FactorState = tuple[int, int]

LocationState = FactorState
KeyState = FactorState
BeefState = FactorState
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

COOK = "cook"
CUT = "cut"

LOCATION_ACTIONS = (UP, DOWN, LEFT, RIGHT)
KEY_ACTIONS = (HEAD_BLACK, HEAD_WHITE, TAIL_BLACK, TAIL_WHITE)
BEEF_ACTIONS = (COOK, CUT)
ACTION_ORDER = LOCATION_ACTIONS + KEY_ACTIONS + BEEF_ACTIONS


# 2. 通用数据结构

@dataclass(frozen=True)
class DirectedTransition:
    """因子图中的一条有向 template：source --action--> target。"""

    source: FactorState
    action: Action
    target: FactorState


def template_id(edge: DirectedTransition) -> str:
    """返回展示和分析使用的稳定 template 标识。"""
    return f"{edge.source}-{edge.action}->{edge.target}"


@dataclass
class FactorGraph:
    """保存一个因子的节点、动作、有向边和绘图信息。"""

    name: FactorName
    nodes: tuple[FactorState, ...]
    actions: tuple[Action, ...]
    transitions: tuple[DirectedTransition, ...]
    labels: Mapping[FactorState, str]
    coordinates: Mapping[FactorState, tuple[float, float]]

    # 因子图建立后内容不变。提前保存两种常用查找结果，避免求解器
    # 在每次动作检查时重新扫描全部有向边。
    _outgoing_lookup: dict = field(init=False, repr=False, compare=False)
    _transition_lookup: dict = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """dataclass 创建对象后会自动执行这里。"""
        self.nodes = tuple(self.nodes)
        self.actions = tuple(self.actions)
        self.transitions = tuple(self.transitions)
        self.labels = dict(self.labels)
        self.coordinates = dict(self.coordinates)

        seen_source_action = []
        for edge in self.transitions:
            if edge.source == edge.target:
                raise ValueError(f"{self.name} 不允许 self-loop: {edge}")
            seen_source_action.append((edge.source, edge.action))
        if len(seen_source_action) != len(set(seen_source_action)):
            raise ValueError(f"{self.name} 的同一状态和动作不能有两个结果")

        outgoing_lookup = {state: [] for state in self.nodes}
        transition_lookup = {}
        for edge in self.transitions:
            outgoing_lookup[edge.source].append(edge)
            transition_lookup[(edge.source, edge.action)] = edge

        self._outgoing_lookup = {
            state: tuple(edges)
            for state, edges in outgoing_lookup.items()
        }
        self._transition_lookup = transition_lookup

    @property
    def templates(self) -> tuple[DirectedTransition, ...]:
        """返回图中的有向 transition templates。"""
        return tuple(dict.fromkeys(self.transitions))

    @property
    def template_ids(self) -> dict[DirectedTransition, str]:
        """返回每个模板的稳定展示标识。"""
        return {edge: template_id(edge) for edge in self.templates}

    def outgoing(self, state: FactorState) -> tuple[DirectedTransition, ...]:
        """返回从 ``state`` 出发的全部有向边。"""
        if state not in self.nodes:
            raise ValueError(f"{self.name} 中不存在状态 {state}")

        return self._outgoing_lookup[state]

    def transition(
        self,
        state: FactorState,
        action: Action,
    ) -> DirectedTransition | None:
        """返回指定的边；动作不可用时返回 ``None``。"""
        if state not in self.nodes:
            raise ValueError(f"{self.name} 中不存在状态 {state}")
        return self._transition_lookup.get((state, action))


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

    def allows(self, conditioning_state: FactorState) -> bool:
        return conditioning_state in self.allowed_condition_states


def rules_allow(
    edge: DirectedTransition,
    rules: tuple[AvailabilityRule, ...],
    conditioning_state: FactorState,
) -> bool:
    """若某条边受到规则控制，则所有相关规则都必须允许它。"""
    for rule in rules:
        if edge in rule.controlled_transitions and not rule.allows(
            conditioning_state
        ):
            return False
    return True


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
    query_set: tuple[JointState, ...]
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
        self.query_set = tuple(self.query_set)
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
        return self.primitive_costs[action]

    def is_terminal(self, state: JointState) -> bool:
        return bool(self.terminal_predicate(state))

    def validate(self) -> None:
        """只检查会使通用环境无法运行的配置错误。"""
        if tuple(graph.name for graph in self.graphs) != FACTOR_ORDER:
            raise ValueError("三张图的 name 必须依次为 L、K、B")
        self._check_actions()
        if not 0 <= self.discount_factor < 1:
            raise ValueError("discount_factor 必须位于 [0, 1)")
        self._check_states()
        self._check_gates(
            self.location_gates,
            self.key_graph,
            self.location_graph,
        )
        self._check_gates(
            self.beef_gates,
            self.location_graph,
            self.beef_graph,
        )

    def _check_actions(self) -> None:
        all_actions = tuple(
            action for graph in self.graphs for action in graph.actions
        )
        if len(all_actions) != len(set(all_actions)):
            raise ValueError("动作必须全局唯一")
        if len(self.action_order) != len(set(self.action_order)):
            raise ValueError("action_order 不能有重复动作")
        if set(self.action_order) != set(all_actions):
            raise ValueError("action_order 必须覆盖全部动作")
        if set(self.primitive_costs) != set(all_actions):
            raise ValueError("primitive_costs 必须覆盖全部动作")

    def _check_states(self) -> None:
        if len(self.initial_state) != 3 or any(
            state not in graph.nodes
            for state, graph in zip(self.initial_state, self.graphs)
        ):
            raise ValueError("initial_state 中有状态不属于对应因子图")
        if not self.query_set:
            raise ValueError("query_set 不能为空")
        for state in self.query_set:
            if len(state) != 3 or any(
                factor_state not in graph.nodes
                for factor_state, graph in zip(state, self.graphs)
            ):
                raise ValueError("query_set 中有状态不属于对应因子图")

    @staticmethod
    def _check_gates(
        rules: tuple[AvailabilityRule, ...],
        condition_graph: FactorGraph,
        target_graph: FactorGraph,
    ) -> None:
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
BOARD_LOCATION = (1, 0)
KITCHEN_LOCATION = (1, 1)

WALLS = frozenset(
    {
        make_undirected_edge((0, 1), (0, 2)),
        make_undirected_edge((2, 1), (2, 2)),
    }
)
DOOR_EDGE = make_undirected_edge((1, 1), (1, 2))

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
        targets_by_action = {
            HEAD_BLACK: (1, tail),
            HEAD_WHITE: (2, tail),
            TAIL_BLACK: (head, 1),
            TAIL_WHITE: (head, 2),
        }
        for action, target in targets_by_action.items():
            if target != source:
                transitions.append(DirectedTransition(source, action, target))
    return tuple(transitions)


def _beef_transitions() -> tuple[DirectedTransition, ...]:
    """建立 Beef 的烹饪和切割进度边。"""
    transitions = []
    for cooking, processing in BEEF_STATES:
        source = (cooking, processing)
        if cooking < 2:
            transitions.append(
                DirectedTransition(source, COOK, (cooking + 1, processing))
            )
        if processing < 2:
            transitions.append(
                DirectedTransition(source, CUT, (cooking, processing + 1))
            )
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


# 4. 四个 task anchors

INITIAL_STATE: JointState = (START_LOCATION, (0, 0), (0, 0))
GOAL_STATE: JointState = (GOAL_LOCATION, (2, 2), (2, 2))

PRIMITIVE_COSTS = {action: 1.0 for action in ACTION_ORDER}

# 这些是声明性的地图元数据。墙已在建图时生效，门在下方筛选规则边；
# 三项本身不参与运行时动作判定。
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
    query_set=(INITIAL_STATE,),
    terminal_predicate=ExactTerminalPredicate(GOAL_STATE),
    primitive_costs=PRIMITIVE_COSTS,
    action_order=ACTION_ORDER,
)


DOOR_TRANSITIONS = tuple(
    edge
    for edge in LOCATION_GRAPH.transitions
    if make_undirected_edge(edge.source, edge.target) == DOOR_EDGE
)
COOK_TRANSITIONS = tuple(
    edge for edge in BEEF_GRAPH.transitions if edge.action == COOK
)
CUT_TRANSITIONS = tuple(
    edge for edge in BEEF_GRAPH.transitions if edge.action == CUT
)

KEY_DOOR_RULE = AvailabilityRule(
    name="white-key-door",
    conditioning_factor=KEY_FACTOR,
    target_factor=LOCATION_FACTOR,
    controlled_transitions=DOOR_TRANSITIONS,
    allowed_condition_states=frozenset({(2, 2)}),
)
KITCHEN_COOKING_RULE = AvailabilityRule(
    name="kitchen-cook-gate",
    conditioning_factor=LOCATION_FACTOR,
    target_factor=BEEF_FACTOR,
    controlled_transitions=COOK_TRANSITIONS,
    allowed_condition_states=frozenset({KITCHEN_LOCATION}),
)
BOARD_CUTTING_RULE = AvailabilityRule(
    name="board-cut-gate",
    conditioning_factor=LOCATION_FACTOR,
    target_factor=BEEF_FACTOR,
    controlled_transitions=CUT_TRANSITIONS,
    allowed_condition_states=frozenset({BOARD_LOCATION}),
)

KEY_GATES_LOCATION_TASK = replace(
    INDEPENDENT_TASK,
    task_name="key_gates_location",
    location_gates=(KEY_DOOR_RULE,),
)
LOCATION_GATES_BEEF_TASK = replace(
    INDEPENDENT_TASK,
    task_name="location_gates_beef",
    beef_gates=(KITCHEN_COOKING_RULE, BOARD_CUTTING_RULE),
)
COMBINED_TASK = replace(
    INDEPENDENT_TASK,
    task_name="combined",
    location_gates=(KEY_DOOR_RULE,),
    beef_gates=(KITCHEN_COOKING_RULE, BOARD_CUTTING_RULE),
)

TASK_CONFIGS = {
    "independent": INDEPENDENT_TASK,
    "key_gates_location": KEY_GATES_LOCATION_TASK,
    "location_gates_beef": LOCATION_GATES_BEEF_TASK,
    "combined": COMBINED_TASK,
}
