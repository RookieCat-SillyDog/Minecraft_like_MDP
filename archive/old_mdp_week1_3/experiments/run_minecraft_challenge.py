"""运行带障碍的 Minecraft-like 挑战地图展示。"""

from math import isclose
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration, find_best_actions
from env.minecraft import MinecraftMDP
from env.minecraft_maps import CHALLENGE_MAP
from experiments.run_minecraft import save_value_policy_figure


FIGURES_DIR = PROJECT_ROOT / "figures"
SOLVER_TOLERANCE = 1e-10
VALUE_TOLERANCE = 1e-8
TIE_TOLERANCE = 1e-8


def setup_plot_style():
    """设置与基线实验一致的中文字体。"""
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    })


def selected_action(policy, state):
    """返回确定性策略在一个状态下选择的动作。"""
    return next(iter(policy[state]))


def compare_values(env, pi_values, vi_values):
    """返回 PI 与 VI 在全部状态上的最大价值差。"""
    differences = [
        (abs(pi_values[state] - vi_values[state]), state)
        for state in env.states
    ]
    return max(differences)


def compare_policies(env, pi_policy, vi_policy, values):
    """记录 PI 和 VI 动作不同的状态，并检查是否为并列最优。"""
    differences = []

    for state in env.states:
        if env.is_terminal(state):
            continue

        pi_action = selected_action(pi_policy, state)
        vi_action = selected_action(vi_policy, state)
        if pi_action == vi_action:
            continue

        best_actions, _ = find_best_actions(
            mdp=env,
            values=values,
            state=state,
            tie_tolerance=TIE_TOLERANCE,
        )
        differences.append({
            "state": state,
            "pi_action": pi_action,
            "vi_action": vi_action,
            "best_actions": best_actions,
            "both_optimal": (
                pi_action in best_actions
                and vi_action in best_actions
            ),
        })

    return differences


def follow_policy(env, policy):
    """执行策略，记录路径、资源顺序和折扣回报。"""
    state = env.initial_state
    path = [state]
    actions = []
    visited = set()
    resource_order = []
    discounted_return = 0.0

    while not env.is_terminal(state):
        if state in visited:
            raise RuntimeError(f"策略进入循环，重复状态为: {state}")
        visited.add(state)

        action = selected_action(policy, state)
        probability, next_state = env.transitions(state, action)[0]
        if not isclose(probability, 1.0):
            raise ValueError("路径展示只适用于确定性转移")

        discounted_return += (
            env.discount_factor ** len(actions) * env.reward(state, action)
        )
        if state[2] == 0 and next_state[2] == 1:
            resource_order.append("wood")
        if state[3] == 0 and next_state[3] == 1:
            resource_order.append("iron")

        actions.append(action)
        path.append(next_state)
        state = next_state

    return {
        "path": path,
        "actions": actions,
        "resource_order": resource_order,
        "discounted_return": discounted_return,
        "terminated": True,
        "has_loop": False,
    }


def save_path_figure(env, pi_result, vi_result):
    """保存一张同时显示 PI 和 VI 最优路径的挑战地图图。"""
    figure, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    results = (("PI", pi_result, "#0072B2"), ("VI", vi_result, "#D55E00"))

    for axis, (name, result, color) in zip(axes, results):
        axis.set_xlim(-0.5, env.grid_size - 0.5)
        axis.set_ylim(env.grid_size - 0.5, -0.5)
        axis.set_aspect("equal")
        axis.set_xticks(range(env.grid_size))
        axis.set_yticks(range(env.grid_size))
        axis.set_xticks(np.arange(-0.5, env.grid_size), minor=True)
        axis.set_yticks(np.arange(-0.5, env.grid_size), minor=True)
        axis.grid(which="minor", color="#BBBBBB")
        axis.tick_params(which="minor", bottom=False, left=False)
        axis.set_xlabel("列")
        axis.set_ylabel("行")

        for row, col in env.obstacles:
            axis.text(col, row, "X", ha="center", va="center", fontsize=24,
                      color="#666666", fontweight="bold")

        for first, second in zip(result["path"], result["path"][1:]):
            axis.annotate(
                "",
                xy=(second[1], second[0]),
                xytext=(first[1], first[0]),
                arrowprops={"arrowstyle": "->", "color": color, "linewidth": 2},
            )

        visit_steps = {}
        for step, state in enumerate(result["path"]):
            visit_steps.setdefault(state[:2], []).append(step)
        for (row, col), steps in visit_steps.items():
            step_text = "/".join(str(step) for step in steps)
            axis.text(col + 0.12, row - 0.18, f"t={step_text}", fontsize=8,
                      bbox={"boxstyle": "round,pad=0.1", "facecolor": "white",
                            "edgecolor": "none", "alpha": 0.8})

        for position, label, marker_color in (
            (env.start, "S", "#777777"),
            (env.wood, "W", "#009E73"),
            (env.iron, "I", "#0072B2"),
            (env.factory, "F", "#D55E00"),
        ):
            axis.scatter(position[1], position[0], s=260, color=marker_color,
                         edgecolor="white", linewidth=1.5, zorder=3)
            axis.text(position[1], position[0], label, ha="center", va="center",
                      color="white", fontweight="bold", zorder=4)

        order = " -> ".join(result["resource_order"])
        axis.set_title(f"{name}: {len(result['actions'])} 步，{order}")

    figure.suptitle("Minecraft-like 挑战地图最优路径（数字为到达步数）")
    figure.tight_layout()
    FIGURES_DIR.mkdir(exist_ok=True)
    png_path = FIGURES_DIR / "day10_minecraft_challenge_paths.png"
    svg_path = FIGURES_DIR / "day10_minecraft_challenge_paths.svg"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight")
    plt.close(figure)
    return png_path, svg_path


def print_result(name, result):
    """打印一个策略的简洁展示结果。"""
    print(
        f"{name}：{len(result['actions'])} 步，"
        f"资源顺序={' -> '.join(result['resource_order'])}，"
        f"终止={result['terminated']}，循环={result['has_loop']}，"
        f"折扣回报={result['discounted_return']:.10f}"
    )


def main():
    """运行挑战地图，并输出可直接记录的验证结果。"""
    setup_plot_style()
    env = MinecraftMDP(map_config=CHALLENGE_MAP)
    pi_solver = PolicyIteration(env, evaluation_tolerance=SOLVER_TOLERANCE)
    vi_solver = ValueIteration(env, tolerance=SOLVER_TOLERANCE)
    pi_policy, pi_values = pi_solver.solve()
    vi_policy, vi_values = vi_solver.solve()


    max_value_difference, max_state = compare_values(env, pi_values, vi_values)
    policy_differences = compare_policies(
        env,
        pi_policy,
        vi_policy,
        vi_values,
    )
    pi_result = follow_policy(env, pi_policy)
    vi_result = follow_policy(env, vi_policy)
    if max_value_difference > VALUE_TOLERANCE:
        raise RuntimeError("PI 与 VI 的最优价值不一致")

    if any(not item["both_optimal"] for item in policy_differences):
        raise RuntimeError("部分策略差异不能由并列最优动作解释")

    for name, values, result in (
        ("PI", pi_values, pi_result),
        ("VI", vi_values, vi_result),
    ):
        if not result["terminated"] or result["has_loop"]:
            raise RuntimeError(f"{name} 策略未能正常终止")
        if not isclose(values[env.initial_state], result["discounted_return"],
                         abs_tol=VALUE_TOLERANCE):
            raise RuntimeError(f"{name} 的起点价值与路径回报不一致")

    figure_paths = []
    figure_paths.extend(save_value_policy_figure(
        env,
        pi_policy,
        pi_values,
        "Policy Iteration（挑战地图）",
        "day10_minecraft_challenge_pi_value_policy",
    ))
    figure_paths.extend(save_value_policy_figure(
        env,
        vi_policy,
        vi_values,
        "Value Iteration（挑战地图）",
        "day10_minecraft_challenge_vi_value_policy",
    ))
    figure_paths.extend(save_path_figure(env, pi_result, vi_result))
    print(env.render())
    print("\n挑战地图结果：")
    print(f"地图：{env.map_config.name}")
    print(f"可达状态数：{len(env.states)}")
    print(f"PI/VI 最大价值差：{max_value_difference:.12g}")
    if max_value_difference != 0.0:
        print(f"最大差值状态：{max_state}")
    print(f"策略动作不同的状态数：{len(policy_differences)}")
    for item in policy_differences:
        best_names = [
            env.ACTION_NAMES[action]
            for action in item["best_actions"]
        ]
        print(
            f"状态 {item['state']}："
            f"PI={env.ACTION_NAMES[item['pi_action']]}，"
            f"VI={env.ACTION_NAMES[item['vi_action']]}，"
            f"并列最优={best_names}"
        )
    print_result("PI", pi_result)
    print_result("VI", vi_result)
    print(f"PI 迭代轮数：{pi_solver.iterations}")
    print(f"VI 迭代轮数：{vi_solver.iterations}")
    print("结果图：")
    for path in figure_paths:
        print(path)


if __name__ == "__main__":
    main()
