"""在 GridWorld 上运行 Value Iteration，并与 Policy Iteration 比较。"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration, find_best_actions
from env.gridworld import GridWorld
from experiments.run_policy_iteration import (
    follow_policy,
    get_selected_action,
    print_policy,
    setup_plot_style,
)


# 无论从哪个目录启动 Python，都把图片保存到项目根目录下的 figures/。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "figures"


def compare_values(env, pi_values, vi_values):
    """比较 PI 与 VI 在全部状态上的价值。

    返回 ``(每个状态的价值差, 最大价值差)``。
    """
    differences = {}

    for state in env.states:
        differences[state]=abs(pi_values[state]-vi_values[state])


    max_difference = max(differences.values())



    return differences, max_difference


def find_policy_differences(
    env,
    pi_policy,
    vi_policy,
    values,
    tie_tolerance=1e-8,
):
    """找出 PI 与 VI 选择不同动作的状态，并检查是否并列最优。"""
    records = []

    for state in env.states:
        if env.is_terminal(state):
            continue

        pi_action = get_selected_action(pi_policy, state)
        vi_action = get_selected_action(vi_policy, state)

        if pi_action == vi_action:
            continue

        best_actions, _ = find_best_actions(
            mdp=env,
            values=values,
            state=state,
            tie_tolerance=tie_tolerance,
        )

        both_are_optimal = (
            pi_action in best_actions
            and vi_action in best_actions
        )

        records.append({
            "state": state,
            "pi_action": pi_action,
            "vi_action": vi_action,
            "best_actions": best_actions,
            "both_are_optimal": both_are_optimal,
        })

    return records


def save_policy_figure(env, policy, values):
    """保存 VI 的最优状态价值与策略图。"""
    value_grid = np.full(
        (env.grid_size, env.grid_size),
        np.nan,
    )

    for state, value in values.items():
        row, col = state
        value_grid[row, col] = value

    action_symbols = {
        env.UP: "↑",
        env.DOWN: "↓",
        env.LEFT: "←",
        env.RIGHT: "→",
    }

    figure, axis = plt.subplots(figsize=(7, 5.5))
    image = axis.imshow(value_grid, cmap="YlGnBu")

    for row in range(env.grid_size):
        for col in range(env.grid_size):
            state = (row, col)

            if state in env.obstacles:
                label = "X"
            elif env.is_terminal(state):
                label = f"{values[state]:.2f}\nG"
            else:
                action = get_selected_action(policy, state)
                symbol = action_symbols[action]
                label = f"{values[state]:.2f}\n{symbol}"

                if state == env.initial_state:
                    label += " S"

            axis.text(
                col,
                row,
                label,
                ha="center",
                va="center",
                color="#222222",
            )

    axis.set_title("Value Iteration 最优策略与状态价值")
    axis.set_xlabel("列")
    axis.set_ylabel("行")
    axis.set_xticks(range(env.grid_size))
    axis.set_yticks(range(env.grid_size))

    color_bar = figure.colorbar(image, ax=axis)
    color_bar.set_label("最优状态价值")

    figure.tight_layout()
    figure.savefig(
        FIGURES_DIR / "day05_value_iteration_policy.png",
        dpi=300,
    )
    figure.savefig(
        FIGURES_DIR / "day05_value_iteration_policy.svg"
    )
    plt.close(figure)


def save_convergence_figure(residuals, tolerance):
    """保存 VI 每轮 Bellman residual 的变化曲线。"""
    iterations = range(1, len(residuals) + 1)

    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.plot(
        iterations,
        residuals,
        marker="o",
        linewidth=2,
        color="#0077BB",
        label="Bellman residual",
    )
    axis.axhline(
        tolerance,
        color="#EE7733",
        linestyle="--",
        linewidth=1.5,
        label=f"停止阈值 {tolerance:.0e}",
    )

    axis.set_title("Value Iteration 收敛记录")
    axis.set_xlabel("价值迭代轮次")
    axis.set_ylabel("Bellman residual")
    axis.set_xticks(list(iterations))
    axis.grid(True, alpha=0.3)
    axis.legend(frameon=False)

    figure.tight_layout()
    figure.savefig(
        FIGURES_DIR / "day05_value_iteration_convergence.png",
        dpi=300,
    )
    figure.savefig(
        FIGURES_DIR / "day05_value_iteration_convergence.svg"
    )
    plt.close(figure)


def main():
    """运行 VI 实验，并与 PI 的最优结果交叉验证。"""
    # 第一步：创建同一个环境以及两种算法对象。
    env = GridWorld()

    pi_solver = PolicyIteration(
        mdp=env,
        evaluation_tolerance=1e-10,
        evaluation_max_iterations=10_000,
        max_iterations=1_000,
        tie_tolerance=1e-12,
    )
    vi_solver = ValueIteration(
        mdp=env,
        tolerance=1e-10,
        max_iterations=10_000,
        tie_tolerance=1e-12,
    )


    pi_policy, pi_values = pi_solver.solve()
    vi_policy, vi_values = vi_solver.solve()

    # 第二步：比较全部状态的价值和策略。
    _, max_difference = compare_values(
        env=env,
        pi_values=pi_values,
        vi_values=vi_values,
    )
    policy_differences = find_policy_differences(
        env=env,
        pi_policy=pi_policy,
        vi_policy=vi_policy,
        values=vi_values,
    )
    path = follow_policy(env, vi_policy)

    # 第三步：生成结果图。
    setup_plot_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    save_policy_figure(env, vi_policy, vi_values)
    save_convergence_figure(
        vi_solver.residuals,
        vi_solver.tolerance,
    )

    # 第四步：打印便于检查和写报告的实验结果。
    print(env.render())
    print("\n价值迭代结果：")
    print(f"是否达到停止条件：{vi_solver.converged}")
    print(f"价值迭代轮数：{vi_solver.iterations}")
    print(f"最终残差：{vi_solver.residuals[-1]:.12g}")
    print(f"起点最优价值：{vi_values[env.initial_state]:.8f}")

    print("\nPI/VI 交叉验证：")
    print(f"全部状态最大价值差：{max_difference:.12g}")
    print(f"策略动作不同的状态数：{len(policy_differences)}")

    for record in policy_differences:
        state = record["state"]
        pi_name = env.ACTION_NAMES[record["pi_action"]]
        vi_name = env.ACTION_NAMES[record["vi_action"]]
        print(
            f"状态 {state}：PI={pi_name}，VI={vi_name}，"
            f"是否均为最优动作={record['both_are_optimal']}"
        )

    print_policy(env, vi_policy)

    print(f"\n起点到终点路径，共 {len(path) - 1} 步：")
    print(" -> ".join(str(state) for state in path))

    print("\n结果图已保存到：")
    print(FIGURES_DIR / "day05_value_iteration_policy.png")
    print(FIGURES_DIR / "day05_value_iteration_convergence.png")


if __name__ == "__main__":
    main()
