"""生成 RM 状态价值与最优策略对比图。
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

from src.algorithms.value_iteration import value_iteration
from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import ACTION_DELTAS, OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


def draw_panel(
    ax, env, values, policy, task_state, title, value_range, comparison_cell
):
    heatmap = np.full((env.rows, env.cols), np.nan)
    for position in env.positions:
        heatmap[position] = values[(position, task_state)]

    image = ax.imshow(
        heatmap,
        cmap="viridis",
        vmin=value_range[0],
        vmax=value_range[1],
    )
    ax.set_title(title, fontsize=11)
    ax.set_xticks(range(env.cols))
    ax.set_yticks(range(env.rows))
    ax.set_xticks(np.arange(-0.5, env.cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, env.rows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8, alpha=0.7)
    ax.tick_params(which="minor", length=0)

    for row, col in env.walls:
        ax.add_patch(mpatches.Rectangle(
            (col - 0.5, row - 0.5), 1, 1,
            facecolor="#777777", edgecolor="white", linewidth=0.8,
        ))

    labels = {**env._prop_at, env.start: "S"}
    for (row, col), label in labels.items():
        ax.text(
            col - 0.42, row - 0.40, label,
            ha="left", va="top", fontsize=7, fontweight="bold",
            color="#111111",
            bbox={
                "facecolor": "white", "edgecolor": "none",
                "alpha": 0.75, "pad": 0.8,
            },
        )

    for position in env.positions:
        row, col = position
        for action in policy[(position, task_state)]:
            drow, dcol = ACTION_DELTAS[action]
            ax.annotate(
                "",
                xy=(col + dcol * 0.30, row + drow * 0.30),
                xytext=(col, row),
                arrowprops={
                    "arrowstyle": "->", "color": "#111111", "lw": 1.2,
                },
            )

    row, col = comparison_cell
    ax.add_patch(mpatches.Rectangle(
        (col - 0.5, row - 0.5), 1, 1,
        fill=False, edgecolor="#CC3311", linewidth=2.5,
    ))
    return image


def make_policy_figure():
    env = OfficeWorld(load_officeworld_config())
    rm = RewardMachine(load_reward_machine_config("coffee_office"))

    values, action_values, policy, _, _, _ = value_iteration(
        env, rm, gamma=0.99
    )
    shown_states = ("u0", "u1")
    comparison_cell = (4, 3)
    shown_values = [
        values[(position, task_state)]
        for task_state in shown_states
        for position in env.positions
    ]
    value_range = (min(shown_values), max(shown_values))

    fig = plt.figure(figsize=(10.5, 4.8))
    grid = fig.add_gridspec(1, 3, width_ratios=(1, 1, 0.045), wspace=0.24)
    axes = (fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]))
    colorbar_axis = fig.add_subplot(grid[0, 2])
    image = draw_panel(
        axes[0], env, values, policy, "u0",
        "RM state u0: need coffee", value_range, comparison_cell,
    )
    draw_panel(
        axes[1], env, values, policy, "u1",
        "RM state u1: need office", value_range, comparison_cell,
    )
    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("Optimal state value V*(s, u)")

    q_u0 = action_values[(comparison_cell, "u0")]
    q_u1 = action_values[(comparison_cell, "u1")]
    comparison = (
        f"Key cell (4,3):  u0  L={q_u0['L']:.4f}*, R={q_u0['R']:.4f};  "
        f"u1  R={q_u1['R']:.4f}*, L={q_u1['L']:.4f}\n"
        f"Optimal actions: u0={policy[(comparison_cell, 'u0')]}  "
        f"u1={policy[(comparison_cell, 'u1')]}; multiple arrows indicate ties"
    )
    fig.text(0.44, 0.035, comparison, ha="center", fontsize=9)
    fig.subplots_adjust(bottom=0.18)

    output_dir = ROOT / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "policy_comparison.svg"
    png_path = output_dir / "policy_comparison.png"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=450, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: {svg_path}")
    print(f"saved: {png_path}")
    return svg_path, png_path


if __name__ == "__main__":
    make_policy_figure()
