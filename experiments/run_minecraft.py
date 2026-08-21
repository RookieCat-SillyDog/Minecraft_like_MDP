"""在 Minecraft-like 环境上运行 PI 和 VI，并比较实验结果。"""

from math import isclose
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np


# 让脚本既能用 python -m 运行，也能直接用文件路径运行。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration, find_best_actions
from env.minecraft import MinecraftMDP


FIGURES_DIR = PROJECT_ROOT / "figures"
SOLVER_TOLERANCE = 1e-10
VALUE_TOLERANCE = 1e-8
TIE_TOLERANCE = 1e-8

# 五维状态不能只画成一张二维地图，因此按资源状态分成四层。
RESOURCE_LAYERS = (
    (0, 0, "尚未收集资源"),
    (1, 0, "仅有 wood"),
    (0, 1, "仅有 iron"),
    (1, 1, "wood 与 iron 齐全"),
)


def selected_action(policy, state):
    """返回确定性策略在一个状态下选择的动作。"""
    return next(iter(policy[state]))


def compare_values(env, pi_values, vi_values):
    """返回 PI/VI 的最大价值差及其对应状态。"""
    differences = {
        state: abs(pi_values[state] - vi_values[state])
        for state in env.states
    }
    max_state = max(differences, key=differences.get)
    return max_state, differences[max_state]


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
    """从初始状态执行策略，直到终止或发现循环。"""
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
        transitions = env.transitions(state, action)
        if len(transitions) != 1:
            raise ValueError("路径实验只适用于确定性转移")

        probability, next_state = transitions[0]
        if not isclose(probability, 1.0):
            raise ValueError("确定性转移的概率必须为 1")

        step = len(actions)
        reward = env.reward(state, action)
        discounted_return += env.discount_factor ** step * reward

        # 比较前后状态，记录资源第一次从 0 变成 1 的时刻。
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
    }


def shortest_path_length(env):
    """计算当前无障碍地图完成任务所需的最少步数。"""
    def distance(first, second):
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

    wood_first = (
        distance(env.start, env.wood)
        + distance(env.wood, env.iron)
        + distance(env.iron, env.factory)
    )
    iron_first = (
        distance(env.start, env.iron)
        + distance(env.iron, env.wood)
        + distance(env.wood, env.factory)
    )
    return min(wood_first, iron_first)


def setup_plot_style():
    """设置三张实验图共用的字体。"""
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def layer_state(env, row, col, wood, iron):
    """取得资源层中一个位置对应的状态，不可达时返回 None。"""
    state = (row, col, wood, iron, 0)
    if state in env.states:
        return state

    # 资源齐全时进入 factory 会立即变成唯一终止状态。
    if wood == 1 and iron == 1 and (row, col) == env.factory:
        return env.TERMINAL_STATE

    return None


def save_value_policy_figure(env, policy, values, algorithm_name, file_name):
    """把一个算法的价值和策略画成四个资源状态面板。"""
    action_symbols = {
        env.UP: "↑",
        env.DOWN: "↓",
        env.LEFT: "←",
        env.RIGHT: "→",
    }
    position_markers = {
        env.start: "S",
        env.wood: "W",
        env.iron: "I",
        env.factory: "F",
    }

    color_map = plt.get_cmap("YlGnBu").copy()
    color_map.set_bad("#D9D9D9")
    min_value = min(values.values())
    max_value = max(values.values())

    figure, axes = plt.subplots(2, 2, figsize=(11, 10))
    image = None

    for axis, (wood, iron, title) in zip(axes.ravel(), RESOURCE_LAYERS):
        value_grid = np.full((env.grid_size, env.grid_size), np.nan)

        for row in range(env.grid_size):
            for col in range(env.grid_size):
                state = layer_state(env, row, col, wood, iron)
                if state is not None:
                    value_grid[row, col] = values[state]

        image = axis.imshow(
            value_grid,
            cmap=color_map,
            vmin=min_value,
            vmax=max_value,
        )

        for row in range(env.grid_size):
            for col in range(env.grid_size):
                state = layer_state(env, row, col, wood, iron)
                marker = position_markers.get((row, col), "")

                if state is None:
                    label = "不可达"
                elif env.is_terminal(state):
                    label = f"{values[state]:.2f}\nT"
                else:
                    action = selected_action(policy, state)
                    label = f"{values[state]:.2f}\n{action_symbols[action]}"

                if marker:
                    label += f" {marker}"

                axis.text(
                    col,
                    row,
                    label,
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="#222222",
                )

        axis.set_title(f"{title}：w={wood}, i={iron}")
        axis.set_xlabel("列")
        axis.set_ylabel("行")
        axis.set_xticks(range(env.grid_size))
        axis.set_yticks(range(env.grid_size))

    figure.suptitle(
        f"Minecraft-like MDP：{algorithm_name} 最优价值与策略",
        fontsize=15,
    )
    figure.subplots_adjust(
        left=0.07,
        right=0.87,
        bottom=0.06,
        top=0.91,
        wspace=0.22,
        hspace=0.25,
    )
    color_bar_axis = figure.add_axes((0.91, 0.14, 0.02, 0.72))
    color_bar = figure.colorbar(image, cax=color_bar_axis)
    color_bar.set_label("最优状态价值")

    png_path = FIGURES_DIR / f"{file_name}.png"
    svg_path = FIGURES_DIR / f"{file_name}.svg"
    figure.savefig(png_path)
    figure.savefig(svg_path)
    plt.close(figure)
    return png_path, svg_path


def save_path_figure(env, pi_result, vi_result):
    """分别绘制 PI 和 VI 路径，并标出每个位置的访问步数。"""
    figure, axes = plt.subplots(1, 2, figsize=(13, 6.5))

    # 路线颜色表示执行这一步之前已经拥有的资源。
    phase_colors = {
        (0, 0): ("未收集资源", "#777777"),
        (1, 0): ("仅有 wood", "#009E73"),
        (0, 1): ("仅有 iron", "#0072B2"),
        (1, 1): ("资源齐全", "#D55E00"),
    }
    special_positions = (
        (env.start, "S", "#777777"),
        (env.wood, "W", "#009E73"),
        (env.iron, "I", "#0072B2"),
        (env.factory, "F", "#D55E00"),
    )

    for axis, (name, result) in zip(
        axes,
        (("PI", pi_result), ("VI", vi_result)),
    ):
        axis.set_xlim(-0.5, env.grid_size - 0.5)
        axis.set_ylim(env.grid_size - 0.5, -0.5)
        axis.set_aspect("equal")
        axis.set_xticks(range(env.grid_size))
        axis.set_yticks(range(env.grid_size))
        axis.set_xticks(np.arange(-0.5, env.grid_size), minor=True)
        axis.set_yticks(np.arange(-0.5, env.grid_size), minor=True)
        axis.grid(which="minor", color="#BBBBBB", linewidth=0.8)
        axis.tick_params(which="minor", bottom=False, left=False)
        axis.set_xlabel("列")
        axis.set_ylabel("行")

        order = " → ".join(result["resource_order"])
        axis.set_title(
            f"{name}：{len(result['actions'])} 步，{order}"
        )

        # 每一段单独画，颜色显示这一步开始前的资源状态。
        for first, second in zip(result["path"], result["path"][1:]):
            _, color = phase_colors[(first[2], first[3])]
            first_row, first_col = first[:2]
            second_row, second_col = second[:2]

            axis.plot(
                (first_col, second_col),
                (first_row, second_row),
                color=color,
                linewidth=3,
                zorder=2,
            )
            axis.annotate(
                "",
                xy=(
                    first_col + 0.72 * (second_col - first_col),
                    first_row + 0.72 * (second_row - first_row),
                ),
                xytext=(
                    first_col + 0.35 * (second_col - first_col),
                    first_row + 0.35 * (second_row - first_row),
                ),
                arrowprops={
                    "arrowstyle": "->",
                    "color": color,
                    "linewidth": 1.6,
                },
                zorder=3,
            )

        # 一个位置可能被多次访问，例如 t=8/16 表示第 8、16 步到达。
        visit_steps = {}
        for step, state in enumerate(result["path"]):
            position = state[:2]
            visit_steps.setdefault(position, []).append(step)

        for (row, col), steps in visit_steps.items():
            step_text = "/".join(str(step) for step in steps)
            axis.text(
                col + 0.18,
                row - 0.20,
                f"t={step_text}",
                ha="left",
                va="center",
                fontsize=7.5,
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.82,
                },
                zorder=4,
            )

        for (row, col), label, color in special_positions:
            axis.scatter(
                col,
                row,
                s=300,
                color=color,
                edgecolor="white",
                linewidth=1.5,
                zorder=5,
            )
            axis.text(
                col,
                row,
                label,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                zorder=6,
            )

    # 用空线条创建统一图例，避免在两个面板中重复说明颜色。
    legend_handles = []
    for label, color in phase_colors.values():
        handle, = axes[0].plot([], [], color=color, linewidth=3, label=label)
        legend_handles.append(handle)

    figure.suptitle(
        "Minecraft-like MDP 最优路径（t 表示到达步数）",
        fontsize=15,
    )
    figure.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=4,
        frameon=False,
    )
    figure.tight_layout(rect=(0, 0.08, 1, 0.94))

    png_path = FIGURES_DIR / "day09_minecraft_optimal_paths.png"
    svg_path = FIGURES_DIR / "day09_minecraft_optimal_paths.svg"
    figure.savefig(png_path)
    figure.savefig(svg_path)
    plt.close(figure)
    return png_path, svg_path


def print_path(env, name, result):
    """逐步打印一个算法从起点到终点的路径。"""
    print(
        f"\n{name} 最优路径：{len(result['actions'])} 步，"
        f"资源顺序={' -> '.join(result['resource_order'])}"
    )

    for step, action in enumerate(result["actions"], start=1):
        state = result["path"][step - 1]
        next_state = result["path"][step]
        print(
            f"{step:2d}. {state} --{env.ACTION_NAMES[action]}--> "
            f"{next_state}"
        )

    print(f"路径折扣回报：{result['discounted_return']:.10f}")


def main():
    """按照创建、求解、比较、检查、输出的顺序运行实验。"""
    # 1. 同一个环境分别交给 PI 和 VI，算法文件不需要知道这是 Minecraft。
    env = MinecraftMDP()
    pi_solver = PolicyIteration(
        mdp=env,
        evaluation_tolerance=SOLVER_TOLERANCE,
        tie_tolerance=1e-12,
    )
    vi_solver = ValueIteration(
        mdp=env,
        tolerance=SOLVER_TOLERANCE,
        tie_tolerance=1e-12,
    )

    # 2. 求解两个最优策略和价值函数。
    pi_policy, pi_values = pi_solver.solve()
    vi_policy, vi_values = vi_solver.solve()

    # 3. 比较全部可达状态，并从初始状态实际执行两个策略。
    max_state, max_value_difference = compare_values(
        env,
        pi_values,
        vi_values,
    )
    policy_differences = compare_policies(
        env,
        pi_policy,
        vi_policy,
        vi_values,
    )
    pi_result = follow_policy(env, pi_policy)
    vi_result = follow_policy(env, vi_policy)

    # 4. 核对 Day 9 的三个核心条件，异常时直接停止并报告原因。
    if max_value_difference > VALUE_TOLERANCE:
        raise RuntimeError("PI 与 VI 的最优价值不一致")

    if any(not item["both_optimal"] for item in policy_differences):
        raise RuntimeError("部分策略差异不能由并列最优动作解释")

    expected_steps = shortest_path_length(env)
    valid_orders = (["wood", "iron"], ["iron", "wood"])
    for name, values, result in (
        ("PI", pi_values, pi_result),
        ("VI", vi_values, vi_result),
    ):
        if len(result["actions"]) != expected_steps:
            raise RuntimeError(f"{name} 没有得到最短路径")
        if result["resource_order"] not in valid_orders:
            raise RuntimeError(f"{name} 没有完整收集两种资源")
        if not isclose(
            values[env.initial_state],
            result["discounted_return"],
            abs_tol=VALUE_TOLERANCE,
        ):
            raise RuntimeError(f"{name} 的起点价值与路径回报不一致")

    # 5. 保存按资源状态分层的价值、策略和路径图。
    setup_plot_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    figure_paths = []
    figure_paths.extend(save_value_policy_figure(
        env,
        pi_policy,
        pi_values,
        "Policy Iteration",
        "day09_minecraft_pi_value_policy",
    ))
    figure_paths.extend(save_value_policy_figure(
        env,
        vi_policy,
        vi_values,
        "Value Iteration",
        "day09_minecraft_vi_value_policy",
    ))
    figure_paths.extend(save_path_figure(env, pi_result, vi_result))

    # 6. 打印可直接用于检查和记录的结果。
    print(env.render())
    print("\n算法收敛结果：")
    print(
        f"PI：{pi_solver.iterations} 轮，"
        f"起点价值={pi_values[env.initial_state]:.10f}"
    )
    print(
        f"VI：{vi_solver.iterations} 轮，"
        f"起点价值={vi_values[env.initial_state]:.10f}，"
        f"最终残差={vi_solver.residuals[-1]:.12g}"
    )

    print("\nPI/VI 交叉验证：")
    print(f"可达状态数：{len(env.states)}")
    print(f"最大价值差：{max_value_difference:.12g}")
    if max_value_difference == 0.0:
        print("全部可达状态的 PI/VI 价值完全一致")
    else:
        print(f"最大价值差对应状态：{max_state}")
    print(f"策略动作不同的状态数：{len(policy_differences)}")
    print("所有不同动作均为并列最优：True")

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

    print(f"\n理论最短路径长度：{expected_steps} 步")
    print_path(env, "PI", pi_result)
    print_path(env, "VI", vi_result)

    print("\n结果图已保存：")
    for path in figure_paths:
        print(path)


if __name__ == "__main__":
    main()
