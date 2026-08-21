"""Day 8：枚举 Minecraft-like MDP 的状态和转移。"""

from collections import deque
from itertools import product
from math import isclose
from pathlib import Path
import sys

# 允许使用 ``python experiments/enumerate_minecraft_states.py`` 直接运行。
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from env.minecraft import MinecraftMDP
from experiments.minecraft_state_graph import save_partial_state_graph


def make_theoretical_states(env):
    """直接组合五个状态变量，得到 200 个理论状态。"""
    states = []

    for row, col, wood, iron, bridge in product(
        range(env.grid_size),
        range(env.grid_size),
        (0, 1),
        (0, 1),
        (0, 1),
    ):
        states.append((row, col, wood, iron, bridge))

    return states


def enumerate_reachable_states(env):
    """从初始状态开始，用广度优先搜索遍历完整转移图。"""
    queue = deque([env.initial_state])
    visited = {env.initial_state}

    reachable_states = []
    transitions = []

    while queue:
        state = queue.popleft()
        reachable_states.append(state)

        for action in env.actions(state):
            outcomes = env.transitions(state, action)
            probability_sum = sum(
                probability
                for probability, _ in outcomes
            )

            if not isclose(
                probability_sum,
                1.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError(
                    f"状态 {state}、动作 {action} 的"
                    f"转移概率之和不是 1"
                )

            for probability, next_state in outcomes:
                if probability < 0.0:
                    raise ValueError("转移概率不能为负数")

                transition = (
                    state,
                    action,
                    probability,
                    next_state,
                )
                transitions.append(transition)

                # 概率大于 0 的下一状态才是真正可达的状态。
                if probability > 0.0 and next_state not in visited:
                    visited.add(next_state)
                    queue.append(next_state)

    return reachable_states, transitions


def explain_unreachable_state(env, state):
    """说明一个理论状态为什么无法从初始状态到达。"""
    row, col, wood, iron, bridge = state
    position = (row, col)

    if bridge == 1:
        return "bridge=1，但状态不是唯一终止状态"

    if position == env.wood and wood == 0:
        return "位于 wood，但 wood 标志仍为 0"

    if position == env.iron and iron == 0:
        return "位于 iron，但 iron 标志仍为 0"

    if position == env.factory and wood == 1 and iron == 1:
        return "资源齐全并位于 factory，但 bridge 标志仍为 0"

    return "未被现有状态约束解释"


def analyze_states(env):
    """完成 Day 8 的枚举、分类和一致性检查。"""
    theoretical_states = make_theoretical_states(env)
    reachable_states, transitions = enumerate_reachable_states(env)

    theoretical_set = set(theoretical_states)
    reachable_set = set(reachable_states)
    declared_states = list(env.states)
    declared_set = set(declared_states)

    unreachable_states = [
        state
        for state in theoretical_states
        if state not in reachable_set
    ]

    unreachable_categories = {}

    for state in unreachable_states:
        reason = explain_unreachable_state(env, state)

        if reason not in unreachable_categories:
            unreachable_categories[reason] = []

        unreachable_categories[reason].append(state)

    state_action_pairs = {
        (state, action)
        for state, action, _, _ in transitions
    }

    # 使用字典保存结果，便于直接按名称理解和检查每项统计。
    return {
        "theoretical_states": theoretical_states,
        "reachable_states": reachable_states,
        "unreachable_states": unreachable_states,
        "transitions": transitions,
        "unreachable_categories": unreachable_categories,
        "state_action_count": len(state_action_pairs),
        "declared_duplicate_count": (
            len(declared_states) - len(declared_set)
        ),
        "reachable_duplicate_count": (
            len(reachable_states) - len(reachable_set)
        ),
        "duplicate_transition_count": (
            len(transitions) - len(set(transitions))
        ),
        "missing_from_declared": sorted(
            reachable_set - declared_set
        ),
        "declared_but_unreachable": sorted(
            declared_set - reachable_set
        ),
        "reachable_outside_theory": sorted(
            reachable_set - theoretical_set
        ),
    }


def print_report(env, result):
    """在终端打印 Day 8 的全部验收统计。"""
    print(env.render())
    print("\nDay 8 状态枚举结果：")
    print(f"理论状态组合数：{len(result['theoretical_states'])}")
    print(f"从初始状态实际可达数：{len(result['reachable_states'])}")
    print(f"理论空间中不可达数：{len(result['unreachable_states'])}")

    print("\n转移统计：")
    print(f"状态—动作对数量：{result['state_action_count']}")
    print(f"带概率的转移结果数量：{len(result['transitions'])}")

    print("\n不可达或不合法状态分类：")

    for reason, states in result["unreachable_categories"].items():
        examples = ", ".join(str(state) for state in states[:3])
        print(f"- {reason}：{len(states)} 个；示例：{examples}")

    print("\n重复与一致性检查：")
    print(f"环境声明状态中的重复数：{result['declared_duplicate_count']}")
    print(f"遍历结果中的重复数：{result['reachable_duplicate_count']}")
    print(f"完全重复的转移记录数：{result['duplicate_transition_count']}")
    print(f"遍历可达但环境未声明的状态数：{len(result['missing_from_declared'])}")
    print(f"环境声明但遍历不可达的状态数：{len(result['declared_but_unreachable'])}")
    print(f"落在理论组合之外的可达状态数：{len(result['reachable_outside_theory'])}")


def main():
    """运行状态枚举并生成部分状态转移图。"""
    env = MinecraftMDP()
    result = analyze_states(env)
    png_path, svg_path = save_partial_state_graph(env)

    print_report(env, result)
    print("\n部分状态转移图已保存：")
    print(png_path)
    print(svg_path)


if __name__ == "__main__":
    main()
