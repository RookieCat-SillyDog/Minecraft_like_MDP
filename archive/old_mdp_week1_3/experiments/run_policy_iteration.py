"""在 GridWorld 上运行 Policy Iteration（策略迭代）。

"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from algorithms.policy_iteration import PolicyIteration
from env.gridworld import GridWorld


# 无论从哪个目录启动 Python，都把图片保存到项目根目录下的 figures/。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "figures"


def setup_plot_style():
    """设置中文字体，并让负号正常显示。"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def get_selected_action(policy, state):
    """取得确定性策略在一个状态下选择的动作。"""
    action_probabilities = policy[state]
    action = next(iter(action_probabilities))
    return action


def follow_policy(env, policy):
    """从起点开始执行策略，返回经过的状态列表。
    """
    state = env.initial_state
    path = [state]

    for _ in range(len(env.states)):
        if env.is_terminal(state):
            return path

        action = get_selected_action(policy, state)
        transitions = env.transitions(state, action)

        if len(transitions) != 1:
            raise ValueError("路径展示要求每个动作只有一个转移结果")

        probability, next_state = transitions[0]
        if probability != 1.0:
            raise ValueError("路径展示要求转移概率为 1")

        state = next_state
        path.append(state)

    raise RuntimeError("策略没有在有限步内到达终点")


def print_policy(env, policy):
    """用箭头打印每个位置选择的动作。"""
    action_symbols = {
        env.UP: "↑",
        env.DOWN: "↓",
        env.LEFT: "←",
        env.RIGHT: "→",
    }

    print("\n最优策略：")

    for row in range(env.grid_size):
        symbols_in_row = []

        for col in range(env.grid_size):
            state = (row, col)

            if state in env.obstacles:
                symbol = "X"
            elif env.is_terminal(state):
                symbol = "G"
            else:
                action = get_selected_action(policy, state)
                symbol = action_symbols[action]

            symbols_in_row.append(symbol)

        print(" ".join(symbols_in_row))


def save_policy_figure(env, policy, values):
    """生成包含状态价值和动作箭头的最优策略图。"""
    value_grid = np.full(
        (env.grid_size, env.grid_size),
        np.nan,
    )

    # 将价值字典转换为与地图形状相同的二维数组。
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

    # 在每个格子中写入价值、动作或地图标记。
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

    axis.set_title("GridWorld 最优策略与状态价值")
    axis.set_xlabel("列")
    axis.set_ylabel("行")
    axis.set_xticks(range(env.grid_size))
    axis.set_yticks(range(env.grid_size))

    color_bar = figure.colorbar(image, ax=axis)
    color_bar.set_label("最优状态价值")

    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "day04_optimal_policy.png", dpi=300)
    figure.savefig(FIGURES_DIR / "day04_optimal_policy.svg")
    plt.close(figure)


def save_convergence_figure(history):
    """生成每轮策略变化状态数的折线图。"""
    iteration_numbers = []
    changed_state_counts = []

    for record in history:
        iteration_numbers.append(record["iteration"])
        changed_state_counts.append(record["changed_states"])

    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.plot(
        iteration_numbers,
        changed_state_counts,
        marker="o",
        linewidth=2,
        color="#0077BB",
    )

    axis.set_title("Policy Iteration 收敛记录")
    axis.set_xlabel("策略迭代轮次")
    axis.set_ylabel("策略变化状态数")
    axis.set_xticks(iteration_numbers)
    axis.set_yticks(range(max(changed_state_counts) + 1))
    axis.grid(True, alpha=0.3)

    figure.tight_layout()
    figure.savefig(
        FIGURES_DIR / "day04_policy_iteration_convergence.png",
        dpi=300,
    )
    figure.savefig(
        FIGURES_DIR / "day04_policy_iteration_convergence.svg"
    )
    plt.close(figure)


def main():
    """运行完整的GridWorld 实验。"""
    # 第一步：创建环境和算法对象。
    env = GridWorld()
    solver = PolicyIteration(
        mdp=env,
        evaluation_tolerance=1e-8,
        evaluation_max_iterations=10_000,
        max_iterations=1_000,
        tie_tolerance=1e-12,
    )

    # 第二步：运行算法并取得结果。
    policy, values = solver.solve()
    path = follow_policy(env, policy)

    # 第三步：创建输出目录并保存图片。
    setup_plot_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    save_policy_figure(env, policy, values)
    save_convergence_figure(solver.history)

    # 第四步：打印便于检查的实验结果。
    print(env.render())
    print("\n策略迭代结果：")
    print(f"是否稳定收敛：{solver.converged}")
    print(f"策略迭代轮数：{solver.iterations}")
    print(f"起点最优价值：{values[env.initial_state]:.8f}")

    print("\n每轮记录：")
    for record in solver.history:
        print(
            f"第 {record['iteration']} 轮："
            f"策略评估 {record['evaluation_iterations']} 次，"
            f"改变 {record['changed_states']} 个状态"
        )

    print_policy(env, policy)

    print(f"\n起点到终点路径，共 {len(path) - 1} 步：")
    print(" -> ".join(str(state) for state in path))

    print("\n结果图已保存到：")
    print(FIGURES_DIR / "day04_optimal_policy.png")
    print(FIGURES_DIR / "day04_policy_iteration_convergence.png")


if __name__ == "__main__":
    main()
