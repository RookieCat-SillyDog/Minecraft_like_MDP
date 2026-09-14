"""Factored GridWorld 的未折扣最短路径计算。"""

from collections import deque

from env.factored_minecraft.maps import location


def distances_to_terminal(env):
    """用反向 BFS 计算每个可达状态到终止集合的最短成本。"""
    predecessors = {state: [] for state in env.states}

    for state in env.states:
        for action in env.actions(state):
            next_state = env.transitions(state, action)[0][1]
            predecessors[next_state].append(state)

    terminal_states = [state for state in env.states if env.is_terminal(state)]
    distances = {state: 0 for state in terminal_states}
    queue = deque(terminal_states)

    while queue:
        state = queue.popleft()
        for predecessor in predecessors[state]:
            if predecessor not in distances:
                distances[predecessor] = distances[state] + 1
                queue.append(predecessor)

    return distances


def optimal_actions(env, distances, state):
    """返回单位步成本下的完整最优动作集合。"""
    return frozenset(
        action
        for action in env.actions(state)
        if distances[env.transitions(state, action)[0][1]]
        == distances[state] - 1
    )


def route_costs(env):
    """分别计算至少穿过一次 Door 和从不穿过 Door 的最短成本。"""
    start = (env.initial_state, False)
    distances = {start: 0}
    queue = deque([start])
    costs = {}

    while queue:
        state, used_door = queue.popleft()

        if env.is_terminal(state):
            costs.setdefault(used_door, distances[(state, used_door)])
            continue

        for action in env.actions(state):
            next_state = env.transitions(state, action)[0][1]
            crossed_door = (
                frozenset((state[location], next_state[location]))
                == env.map_config.door_edge
            )
            next_record = (next_state, used_door or crossed_door)

            if next_record not in distances:
                distances[next_record] = distances[(state, used_door)] + 1
                queue.append(next_record)

    return costs[True], costs[False]
