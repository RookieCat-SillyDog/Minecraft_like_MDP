"""在 GridWorld 上运行迭代式策略评估并生成结果图。"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from algorithms.policy_evaluation import PolicyEvaluation, uniform_random_policy
from env.gridworld import GridWorld


FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"


def setup_plot_style():
    """设置两张图共用的字体和外观。"""
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "savefig.dpi": 450,
        "savefig.bbox": "tight",
    })


def print_value_grid(env, values):
    """按照地图位置打印每个状态的价值。"""
    print("\n随机策略价值表：")

    for row in range(env.grid_size):
        row_values = []

        for col in range(env.grid_size):
            state = (row, col)

            if state in env.obstacles:
                row_values.append("   X   ")
            else:
                row_values.append(f"{values[state]:7.2f}")

        print(" ".join(row_values))


def save_value_figure(env, values):
    """保存随机策略的状态价值热力图。"""
    value_grid = np.full((env.grid_size, env.grid_size), np.nan)

    for state, value in values.items():
        row, col = state
        value_grid[row, col] = value

    colors = ["#F2E8CF", "#76B7B2", "#4E79A7"]
    color_map = LinearSegmentedColormap.from_list("value_map", colors)
    color_map.set_bad("#BDBDBD")

    figure, axis = plt.subplots(figsize=(7, 5.5))
    image = axis.imshow(value_grid, cmap=color_map)

    for row in range(env.grid_size):
        for col in range(env.grid_size):
            state = (row, col)

            if state in env.obstacles:
                label = "X"
            else:
                label = f"{values[state]:.2f}"

                if state == env.start:
                    label += "\nS"
                elif state == env.goal:
                    label += "\nG"

            axis.text(
                col,
                row,
                label,
                ha="center",
                va="center",
                color="#222222",
            )

    axis.set_title("GridWorld 均匀随机策略状态价值")
    axis.set_xlabel("列")
    axis.set_ylabel("行")
    axis.set_xticks(range(env.grid_size))
    axis.set_yticks(range(env.grid_size))

    color_bar = figure.colorbar(image, ax=axis)
    color_bar.set_label("状态价值")

    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "day03_random_policy_values.png")
    figure.savefig(FIGURES_DIR / "day03_random_policy_values.svg")
    plt.close(figure)


def save_residual_figure(residuals, tolerance):
    """保存每轮 Bellman residual 的变化曲线。"""
    iterations = range(1, len(residuals) + 1)

    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.semilogy(
        iterations,
        residuals,
        color="#0077BB",
        linewidth=2,
        label="Bellman residual",
    )
    axis.axhline(
        tolerance,
        color="#EE7733",
        linestyle="--",
        linewidth=1.5,
        label=f"收敛阈值 {tolerance:.0e}",
    )

    axis.set_title("迭代式策略评估收敛过程")
    axis.set_xlabel("迭代次数")
    axis.set_ylabel("Bellman residual（对数刻度）")
    axis.grid(True, alpha=0.3)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.legend(frameon=False)

    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "day03_bellman_residual.png")
    figure.savefig(FIGURES_DIR / "day03_bellman_residual.svg")
    plt.close(figure)


def main():
    """创建环境和随机策略，然后运行策略评估。"""
    env = GridWorld()
    policy = uniform_random_policy(env)

    evaluator = PolicyEvaluation(
        mdp=env,
        policy=policy,
        tolerance=1e-8,
        max_iterations=10_000,
    )

    values = evaluator.evaluate()

    setup_plot_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    save_value_figure(env, values)
    save_residual_figure(evaluator.residuals, evaluator.tolerance)

    print(env.render())
    print("\n策略评估结果：")
    print(f"是否收敛：{evaluator.converged}")
    print(f"迭代次数：{evaluator.iterations}")
    print(f"最终残差：{evaluator.residuals[-1]:.12g}")

    print_value_grid(env, values)

    print("\n结果图已保存：")
    print(FIGURES_DIR / "day03_random_policy_values.png")
    print(FIGURES_DIR / "day03_bellman_residual.png")


if __name__ == "__main__":
    main()
