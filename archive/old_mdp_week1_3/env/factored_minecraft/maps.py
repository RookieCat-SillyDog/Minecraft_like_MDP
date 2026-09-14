"""三因子 Minecraft 的世界定义。"""

from dataclasses import dataclass


Action = str
GridState = tuple[int, int]
FactorState = GridState | str
JointState = tuple[GridState, str, str]

location, key, beef = range(3)

location_states = tuple((row, col) for row in range(3) for col in range(3))
key_states = ("blank", "shallow blue", "blue")
beef_states = ("raw", "medium", "well")

action_spec = (
    ("up", location),
    ("down", location),
    ("left", location),
    ("right", location),
    ("dye", key),
    ("cook", beef),
)

landmarks = {
    "start": (0, 0),
    "kitchen": (0, 1),
    "goal": (2, 1),
}

initial_state = (landmarks["start"], "blank", "raw")
terminal_states = frozenset(
    (landmarks["goal"], key_state, "well") for key_state in key_states
)

action_deltas = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}

# 两张地图共享一面 edge wall，不占用格子。
wall_edges = (frozenset(((1, 1), (1, 2))),)

location_moves = {}
for source in location_states:
    for action, (row_change, col_change) in action_deltas.items():
        target = (source[0] + row_change, source[1] + col_change)
        edge = frozenset((source, target))
        if target in location_states and edge not in wall_edges:
            location_moves[(source, action)] = target

key_moves = {
    ("blank", "dye"): "shallow blue",
    ("shallow blue", "dye"): "blue",
}
beef_moves = {
    ("raw", "cook"): "medium",
    ("medium", "cook"): "well",
}

factor_states = (location_states, key_states, beef_states)
factor_moves = (location_moves, key_moves, beef_moves)


@dataclass(frozen=True)
class MapConfig:
    """两张地图只需要记录不同的 Door edge。"""

    door_edge: frozenset[GridState]

    action_spec = action_spec
    factor_states = factor_states
    factor_moves = factor_moves
    initial_state = initial_state
    terminal_states = terminal_states
    landmarks = landmarks
    discount_factor = 0.95


# Map A：Door edge = {S, C} = {(0,0), (0,1)}。
map_a = MapConfig(frozenset(((0, 0), (0, 1))))

# Map B：Door edge = {(1,1), G} = {(1,1), (2,1)}。
map_b = MapConfig(frozenset(((1, 1), (2, 1))))
