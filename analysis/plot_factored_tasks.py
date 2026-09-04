"""绘制 Map A/B 的地图、策略变化和 Door leverage。"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

from analysis.analyze_factored_tasks import analyze_map
from env.factored_minecraft.maps import (
    beef_states,
    location_moves,
    map_a,
    map_b,
    wall_edges,
)


FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"

EDGE_COLOR = "#B5B5B5"
DOOR_COLOR = "#EE7733"
FLIP_COLOR = "#0077BB"
WALL_COLOR = "#333333"
LANDMARK_COLORS = {
    "start": "#009988",
    "kitchen": "#EE7733",
    "goal": "#CC3311",
}


def setup_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 450,
        "savefig.bbox": "tight",
    })


def save_figure(figure, name):
    FIGURES_DIR.mkdir(exist_ok=True)
    figure.savefig(FIGURES_DIR / f"{name}.png", dpi=450)
    figure.savefig(FIGURES_DIR / f"{name}.svg")
    plt.close(figure)
    print(f"saved: {name}.png, {name}.svg")


def draw_map(axis, name, map_config):
    drawn_edges = set()
    for (source, _action), target in location_moves.items():
        edge = frozenset((source, target))
        if edge in drawn_edges:
            continue
        drawn_edges.add(edge)

        color = DOOR_COLOR if edge == map_config.door_edge else EDGE_COLOR
        width = 4 if edge == map_config.door_edge else 1.5
        axis.plot(
            (source[1], target[1]),
            (source[0], target[0]),
            color=color,
            linewidth=width,
            zorder=1,
        )

    for wall in wall_edges:
        first, second = tuple(wall)
        wall_x = (first[1] + second[1]) / 2
        wall_y = (first[0] + second[0]) / 2
        if first[0] == second[0]:
            x_points = (wall_x, wall_x)
            y_points = (wall_y - 0.16, wall_y + 0.16)
        else:
            x_points = (wall_x - 0.16, wall_x + 0.16)
            y_points = (wall_y, wall_y)
        axis.plot(
            x_points,
            y_points,
            color=WALL_COLOR,
            linewidth=5,
            solid_capstyle="round",
            zorder=2,
        )

    landmark_at = {position: label for label, position in map_config.landmarks.items()}
    short_label = {"start": "S", "kitchen": "C", "goal": "G"}

    for row in range(3):
        for col in range(3):
            position = (row, col)
            landmark = landmark_at.get(position)
            color = LANDMARK_COLORS.get(landmark, "#F4F4F4")
            axis.scatter(
                col,
                row,
                s=520,
                color=color,
                edgecolor="#444444",
                linewidth=1,
                zorder=2,
            )
            axis.text(
                col,
                row,
                short_label.get(landmark, ""),
                ha="center",
                va="center",
                color="white" if landmark else "#444444",
                fontweight="bold",
                zorder=3,
            )
            axis.text(col, row + 0.32, str(position), ha="center", fontsize=6.5)

    first, second = tuple(map_config.door_edge)
    door_x = (first[1] + second[1]) / 2
    door_y = (first[0] + second[0]) / 2
    if first[0] == second[0]:
        door_y -= 0.13
        horizontal_alignment = "center"
        vertical_alignment = "bottom"
    else:
        door_x += 0.16
        horizontal_alignment = "left"
        vertical_alignment = "center"
    axis.text(
        door_x,
        door_y,
        "Door\nBlue only",
        ha=horizontal_alignment,
        va=vertical_alignment,
        color=DOOR_COLOR,
        fontsize=7,
        fontweight="bold",
    )
    axis.set_title(name)
    axis.set_xlim(-0.55, 2.55)
    axis.set_ylim(2.55, -0.55)
    axis.set_aspect("equal")
    axis.axis("off")


def plot_maps():
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(9, 3.2),
        gridspec_kw={"width_ratios": [1, 1, 0.8]},
        layout="constrained",
    )

    draw_map(axes[0], "Map A: Door at S-C", map_a)
    draw_map(axes[1], "Map B: Door at (1, 1)-G", map_b)

    dependency_axis = axes[2]
    dependency_axis.set_title("Shared dependency")
    dependency_axis.text(0.1, 0.5, "Key\n(K)", ha="center", va="center")
    dependency_axis.text(0.5, 0.5, "Location\n(L)", ha="center", va="center")
    dependency_axis.text(0.9, 0.5, "Beef\n(B)", ha="center", va="center")
    dependency_axis.annotate("", xy=(0.4, 0.5), xytext=(0.2, 0.5),
                             arrowprops={"arrowstyle": "->", "color": FLIP_COLOR})
    dependency_axis.annotate("", xy=(0.8, 0.5), xytext=(0.6, 0.5),
                             arrowprops={"arrowstyle": "->", "color": FLIP_COLOR})
    dependency_axis.text(0.3, 0.58, "Door", ha="center", fontsize=7)
    dependency_axis.text(0.7, 0.58, "Kitchen", ha="center", fontsize=7)
    dependency_axis.set_xlim(0, 1)
    dependency_axis.set_ylim(0, 1)
    dependency_axis.axis("off")

    handles = [
        Line2D([], [], color=EDGE_COLOR, linewidth=1.5, label="bidirectional move"),
        Line2D([], [], color=DOOR_COLOR, linewidth=4, label="Door edge"),
        Line2D([], [], color=WALL_COLOR, linewidth=5, label="Wall"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=3, frameon=False)
    figure.suptitle("Cost-matched factored GridWorld tasks")
    save_figure(figure, "factored_gridworld_maps")


def metric_grid(values, beef_state):
    grid = np.full((3, 3), np.nan)
    for (location_state, state_beef), value in values.items():
        if state_beef == beef_state:
            grid[location_state] = value
    return grid


def style_grid_axis(axis, beef_state, row_index, column_index):
    axis.set_title(f"Beef = {beef_state.title()}")
    axis.set_xticks(range(3))
    axis.set_yticks(range(3))
    if row_index == 1:
        axis.set_xlabel("col")
    if column_index == 0:
        axis.set_ylabel("row")
    axis.set_xticks(np.arange(-0.5, 3, 1), minor=True)
    axis.set_yticks(np.arange(-0.5, 3, 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=1.5)
    axis.tick_params(which="minor", bottom=False, left=False)
    if row_index == 0:
        axis.tick_params(labelbottom=False)


def plot_policy_changes(results):
    color_map = ListedColormap(["#F2F2F2", FLIP_COLOR])
    color_map.set_bad("#BDBDBD")
    figure, axes = plt.subplots(2, 3, figsize=(7, 5.3), layout="constrained")

    for row, result in enumerate(results):
        for col, beef_state in enumerate(beef_states):
            axis = axes[row, col]
            grid = metric_grid(result["location_policy_changes"], beef_state)
            axis.imshow(grid, cmap=color_map, vmin=0, vmax=1)
            style_grid_axis(axis, beef_state, row, col)

            for location_state in np.ndindex(grid.shape):
                value = grid[location_state]
                text = "T" if np.isnan(value) else str(int(value))
                color = "white" if value == 1 else "#333333"
                axis.text(
                    location_state[1],
                    location_state[0],
                    text,
                    ha="center",
                    va="center",
                    color=color,
                    fontweight="bold",
                )

        axes[row, 0].set_ylabel(
            f"{result['name']}\nrow\n$D_{{K\\to L}}$ = "
            f"{result['d_kl_count']}/{result['context_count']}"
        )

    handles = [
        Patch(facecolor="#F2F2F2", label="0: same optimal-action set"),
        Patch(facecolor=FLIP_COLOR, label="1: changed optimal-action set"),
        Patch(facecolor="#BDBDBD", label="T: terminal context"),
    ]
    figure.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.035),
        ncol=3,
        frameon=False,
    )
    figure.suptitle("Key-induced Location-policy change: Blank vs Blue")
    save_figure(figure, "factored_gridworld_policy_changes")


def plot_door_leverage(results):
    maximum = max(
        value
        for result in results
        for value in result["door_leverage"].values()
    )
    color_map = matplotlib.colormaps["YlOrBr"].copy()
    color_map.set_bad("#BDBDBD")
    figure, axes = plt.subplots(2, 3, figsize=(7, 5.3), layout="constrained")

    for row, result in enumerate(results):
        for col, beef_state in enumerate(beef_states):
            axis = axes[row, col]
            grid = metric_grid(result["door_leverage"], beef_state)
            image = axis.imshow(grid, cmap=color_map, vmin=0, vmax=maximum)
            style_grid_axis(axis, beef_state, row, col)

            for location_state in np.ndindex(grid.shape):
                value = grid[location_state]
                text = "T" if np.isnan(value) else str(int(value))
                color = "white" if value > maximum / 2 else "#333333"
                axis.text(
                    location_state[1],
                    location_state[0],
                    text,
                    ha="center",
                    va="center",
                    color=color,
                    fontweight="bold",
                )

        axes[row, 0].set_ylabel(
            f"{result['name']}\nrow\nmean $\\Gamma_D$ = "
            f"{result['door_leverage_total']}/{result['context_count']}"
        )

    figure.colorbar(
        image,
        ax=axes,
        shrink=0.8,
        label="Extra optimal steps after removing Door",
    )
    figure.suptitle("Door coupling leverage $\\Gamma_D(l,b)$ at Key = Blue")
    save_figure(figure, "factored_gridworld_door_leverage")


def main():
    setup_style()
    results = [
        analyze_map("Map A", map_a),
        analyze_map("Map B", map_b),
    ]
    plot_maps()
    plot_policy_changes(results)
    plot_door_leverage(results)


if __name__ == "__main__":
    main()
