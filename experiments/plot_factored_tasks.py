"""绘制 week3 三因子任务的展示图。

数据来源：
- 三张 component graphs 来自 ``env/factored_tasks.py`` 的 ``FactorGraph``；
- 耦合规则标注来自 ``combined`` anchor 配置里的 ``coupling_rules``；
- 价值切片来自对 ``combined`` 环境运行一次 Value Iteration；
- anchor 对比数据来自 ``experiments/analyze_factored_tasks.py`` 的
  ``analyze_task()`` 返回结果。

运行方式（仓库根目录）：

    python -B -m experiments.plot_factored_tasks
"""

from collections import deque
from pathlib import Path
import sys

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


# 让脚本既能用 python -m 运行，也能直接用文件路径运行。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.value_iteration import ValueIteration
from env.factored_minecraft import FactoredMinecraftMDP
from env.factored_tasks import (
    BEEF_FACTOR,
    KEY_FACTOR,
    LOCATION_FACTOR,
    TASK_CONFIGS,
    rules_allow,
)
from experiments.analyze_factored_tasks import SOLVER_TOLERANCE, analyze_task


FIGURES_DIR = PROJECT_ROOT / "figures"

# Day 15 规划中预先固定的图形输入。
COMBINED_CONFIG = TASK_CONFIGS["combined"]
SLICE_BEEF_STATES = ((0, 0), (1, 1), (2, 2))

# 少量固定颜色：普通边、两类规则边和地标节点。
NORMAL_EDGE_COLOR = "#999999"
RULE_EDGE_COLORS = ("#D62728", "#1F77B4", "#2CA02C")
LANDMARK_COLORS = {
    "start": "#2CA02C",
    "goal": "#D62728",
    "board": "#8C564B",
    "kitchen": "#FF7F0E",
}


def setup_style():
    """设置各图共用的简洁样式；图中文字只用英文和数学记号。"""
    plt.rcParams.update({
        "font.sans-serif": ["DejaVu Sans"],
        "axes.unicode_minus": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def save_figure(figure, file_name):
    """同时保存 PNG 和 SVG，然后关闭 figure。"""
    png_path = FIGURES_DIR / f"{file_name}.png"
    svg_path = FIGURES_DIR / f"{file_name}.svg"
    figure.savefig(png_path)
    figure.savefig(svg_path)
    plt.close(figure)
    print(f"saved: {png_path.name}, {svg_path.name}")


# 1. 图一：三张 component graphs


def landmark_name(config, location):
    """把 kitchen/board 这类地标位置翻译成配置里的名字。"""
    for name, state in config.location_landmarks.items():
        if state == location:
            return name
    return str(location)


def gate_descriptions(config):
    """把每条受控 transition 映射成一句规则说明。

    说明文字完全来自配置中的 AvailabilityRule，例如
    "needs k=(2, 2)"、"needs kitchen"、"needs board"。
    """
    descriptions = {}
    for rule in config.coupling_rules:
        if rule.conditioning_factor == LOCATION_FACTOR:
            names = sorted({
                landmark_name(config, state)
                for state in rule.allowed_condition_states
            })
            text = "needs " + "/".join(names)
        else:
            states = sorted(rule.allowed_condition_states)
            text = "needs k=" + "/".join(str(state) for state in states)
        for edge in rule.controlled_transitions:
            descriptions[edge] = text
    return descriptions


def draw_edge(axis, start, end, color, linewidth=1.3, curvature=0.0):
    """在两个坐标之间画一个缩短的箭头；双向边稍微错开。"""
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    # 弧线从节点中心附近出发；直线双向边则各向侧面偏移一点。
    if curvature != 0.0:
        offset_x = 0.0
        offset_y = 0.0
    elif delta_x != 0:
        offset_x = 0.0
        offset_y = 0.08 if delta_x > 0 else -0.08
    else:
        offset_x = -0.08 if delta_y > 0 else 0.08
        offset_y = 0.0

    start_point = (start[0] + 0.18 * delta_x + offset_x,
                   start[1] + 0.18 * delta_y + offset_y)
    end_point = (start[0] + 0.82 * delta_x + offset_x,
                 start[1] + 0.82 * delta_y + offset_y)
    axis.annotate(
        "",
        xy=end_point,
        xytext=start_point,
        arrowprops={
            "arrowstyle": "->",
            "color": color,
            "linewidth": linewidth,
            "shrinkA": 0,
            "shrinkB": 0,
            "connectionstyle": f"arc3,rad={curvature}",
        },
        zorder=2,
    )


def draw_factor_nodes(axis, graph, highlighted_states):
    """画出因子图的 9 个节点和文字标签。"""
    for state in graph.nodes:
        x, y = graph.coordinates[state]
        landmark = highlighted_states.get(state)
        node_color = LANDMARK_COLORS.get(landmark, "#F0F0F0")
        axis.scatter(
            x,
            y,
            s=260,
            color=node_color,
            edgecolor="#555555",
            linewidth=1.0,
            zorder=3,
        )
        label = graph.labels[state]
        if landmark is not None:
            label = f"{label}\n{landmark}"
        axis.text(
            x,
            y - 0.42,
            label,
            ha="center",
            va="top",
            fontsize=6.5,
            zorder=4,
        )


def plot_location_panel(axis, config):
    """Location 图：普通移动、双向门规则和地标。"""
    graph = config.location_graph
    descriptions = gate_descriptions(config)
    door_color = RULE_EDGE_COLORS[0]

    for edge in graph.transitions:
        color = door_color if edge in descriptions else NORMAL_EDGE_COLOR
        draw_edge(
            axis,
            graph.coordinates[edge.source],
            graph.coordinates[edge.target],
            color,
        )

    highlighted = {}
    for name, state in config.location_landmarks.items():
        highlighted[state] = name
    draw_factor_nodes(axis, graph, highlighted)

    # 门边中点标一个 D，门的位置来自 edge_landmarks。
    door_edge = config.edge_landmarks["door"]
    door_endpoints = sorted(door_edge)
    first = graph.coordinates[door_endpoints[0]]
    second = graph.coordinates[door_endpoints[1]]
    axis.text(
        (first[0] + second[0]) / 2 + 0.16,
        (first[1] + second[1]) / 2,
        "D",
        ha="left",
        va="center",
        fontsize=8,
        fontweight="bold",
        color=door_color,
        zorder=4,
    )

    axis.set_xlim(-0.6, 2.6)
    axis.set_ylim(2.6, -0.6)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title("Location factor (L)")

    door_text = descriptions[
        next(edge for edge in graph.transitions if edge in descriptions)
    ]
    handles = [
        Line2D([], [], color=NORMAL_EDGE_COLOR, linewidth=1.5, label="move"),
        Line2D([], [], color=door_color, linewidth=1.5, label=f"door ({door_text})"),
    ]
    for name, color in LANDMARK_COLORS.items():
        handles.append(
            Line2D(
                [],
                [],
                marker="o",
                linestyle="",
                markerfacecolor=color,
                markeredgecolor="#555555",
                label=name,
            )
        )
    axis.legend(handles=handles, loc="upper left", fontsize=6, frameon=False)


def plot_key_panel(axis, config):
    """Key 图：四类属性变换动作各用一种颜色。"""
    graph = config.key_graph
    action_colors = {
        "head-black": "#1F77B4",
        "head-white": "#D62728",
        "tail-black": "#2CA02C",
        "tail-white": "#FF7F0E",
    }

    for edge in graph.transitions:
        start = graph.coordinates[edge.source]
        end = graph.coordinates[edge.target]
        distance = abs(end[0] - start[0]) + abs(end[1] - start[1])
        curvature = 0.0
        if distance > 1:
            if end[0] != start[0]:
                curvature = 0.3
            elif start[0] == 0:
                curvature = 0.32
            else:
                curvature = -0.32
        draw_edge(
            axis,
            start,
            end,
            action_colors[edge.action],
            curvature=curvature,
        )

    draw_factor_nodes(axis, graph, {})
    axis.set_xlim(-0.6, 2.6)
    axis.set_ylim(2.6, -0.6)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title("Key factor (K)")

    handles = [
        Line2D([], [], color=color, linewidth=1.5, label=action)
        for action, color in action_colors.items()
    ]
    axis.legend(handles=handles, loc="upper left", fontsize=6, frameon=False)


def plot_beef_panel(axis, config):
    """Beef 图：cook 和 cut 两类模板边，并标注位置条件。"""
    graph = config.beef_graph
    descriptions = gate_descriptions(config)
    cook_color = RULE_EDGE_COLORS[1]
    cut_color = RULE_EDGE_COLORS[2]

    cook_text = None
    cut_text = None
    for edge in graph.transitions:
        if edge in descriptions:
            color = cook_color if edge.action == "cook" else cut_color
            if edge.action == "cook":
                cook_text = descriptions[edge]
            else:
                cut_text = descriptions[edge]
        else:
            color = NORMAL_EDGE_COLOR
        draw_edge(
            axis,
            graph.coordinates[edge.source],
            graph.coordinates[edge.target],
            color,
        )

    draw_factor_nodes(axis, graph, {})
    axis.set_xlim(-0.6, 2.6)
    axis.set_ylim(2.6, -0.6)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title("Beef factor (B)")

    handles = [
        Line2D([], [], color=cook_color, linewidth=1.5, label=f"cook ({cook_text})"),
        Line2D([], [], color=cut_color, linewidth=1.5, label=f"cut ({cut_text})"),
    ]
    axis.legend(handles=handles, loc="upper left", fontsize=6, frameon=False)


def plot_three_factor_graphs(config):
    """画三张 component graphs，并标注 combined 的活跃耦合规则。"""
    figure, axes = plt.subplots(1, 3, figsize=(15, 5.4))
    plot_location_panel(axes[0], config)
    plot_key_panel(axes[1], config)
    plot_beef_panel(axes[2], config)
    figure.suptitle(
        "Three factor component graphs with combined coupling rules",
        fontsize=14,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(figure, "week3_three_factor_graph")


# 2. 图二：combined 的联合价值切片


def plot_value_slices(config):
    """对 combined 求解一次 VI，画三个 Beef 状态的 location-by-key 切片。"""
    env = FactoredMinecraftMDP(config)
    solver = ValueIteration(env, tolerance=SOLVER_TOLERANCE)
    _, values = solver.solve()
    print(
        f"VI on '{config.task_name}': {solver.iterations} iterations, "
        f"{len(env.states)} reachable states"
    )

    location_states = config.location_graph.nodes
    key_states = config.key_graph.nodes

    # 三个切片共用一个 9x9x3 数组；不可达联合状态保持 NaN。
    slice_grids = np.full(
        (len(SLICE_BEEF_STATES), len(location_states), len(key_states)),
        np.nan,
    )
    for beef_index, beef in enumerate(SLICE_BEEF_STATES):
        for row, location in enumerate(location_states):
            for col, key in enumerate(key_states):
                state = (location, key, beef)
                if state in env.states:
                    slice_grids[beef_index, row, col] = values[state]

    vmin = np.nanmin(slice_grids)
    vmax = np.nanmax(slice_grids)
    color_map = matplotlib.colormaps["YlGnBu"].copy()
    color_map.set_bad("#D9D9D9")

    # colorbar 与 tight_layout 不兼容，这里使用 constrained 布局。
    figure, axes = plt.subplots(
        1, 3, figsize=(15, 5.6), layout="constrained",
    )
    for axis, beef, grid in zip(axes, SLICE_BEEF_STATES, slice_grids):
        image = axis.imshow(grid, cmap=color_map, vmin=vmin, vmax=vmax)

        for row in range(len(location_states)):
            for col in range(len(key_states)):
                if np.isnan(grid[row, col]):
                    text = "x"
                    color = "#777777"
                else:
                    text = f"{grid[row, col]:.2f}"
                    color = "#222222"
                axis.text(
                    col,
                    row,
                    text,
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color=color,
                )

        axis.set_title(
            f"beef = {config.beef_graph.labels[beef]} {beef}"
        )
        axis.set_xticks(range(len(key_states)))
        axis.set_xticklabels(
            [config.key_graph.labels[state] for state in key_states],
            rotation=90,
            fontsize=6,
        )
        axis.set_yticks(range(len(location_states)))
        axis.set_yticklabels(
            [str(state) for state in location_states],
            fontsize=6,
        )
        axis.set_xlabel("Key state (head/tail)")
        axis.set_ylabel("Location state (row, col)")

    figure.colorbar(
        image,
        ax=axes,
        shrink=0.85,
        label="optimal value V*",
    )
    figure.suptitle(
        "Combined anchor: V* slices over location x key for fixed beef states "
        "(x = unreachable joint state)",
        fontsize=13,
    )
    save_figure(figure, "week3_joint_value_slices")


# 3. 图三和图四：两个 anchor 间的最短距离差值切片


def theoretical_states(config):
    """枚举配置三张因子图组成的全部 729 个联合状态。"""
    return tuple(
        (location, key, beef)
        for location in config.location_graph.nodes
        for key in config.key_graph.nodes
        for beef in config.beef_graph.nodes
    )


def configured_successors(config, state):
    """返回理论状态空间中由配置允许的后继状态。"""
    if config.is_terminal(state):
        return ()

    location, key, beef = state
    successors = []
    for action in config.action_order:
        factor = config.factor_for_action(action)

        if factor == LOCATION_FACTOR:
            edge = config.location_graph.transition(location, action)
            if edge is not None and rules_allow(
                edge,
                config.location_gates,
                key,
            ):
                successors.append((edge.target, key, beef))

        elif factor == KEY_FACTOR:
            edge = config.key_graph.transition(key, action)
            if edge is not None:
                successors.append((location, edge.target, beef))

        elif factor == BEEF_FACTOR:
            edge = config.beef_graph.transition(beef, action)
            if edge is not None and rules_allow(
                edge,
                config.beef_gates,
                location,
            ):
                successors.append((location, key, edge.target))

    return tuple(successors)


def distances_to_terminal(config):
    """在完整理论状态空间中用反向 BFS 计算到终止状态的最短步数。"""
    states = theoretical_states(config)
    predecessors = {state: [] for state in states}
    terminal_states = []

    for state in states:
        if config.is_terminal(state):
            terminal_states.append(state)
            continue
        for next_state in configured_successors(config, state):
            predecessors[next_state].append(state)

    distances = {state: 0 for state in terminal_states}
    queue = deque(terminal_states)
    while queue:
        state = queue.popleft()
        for predecessor in predecessors[state]:
            if predecessor not in distances:
                distances[predecessor] = distances[state] + 1
                queue.append(predecessor)

    return distances


def distance_delta_grids(reference_distances, coupled_distances, config):
    """按固定 Beef 状态构造 location-by-key 的整数距离差值网格。"""
    location_states = config.location_graph.nodes
    key_states = config.key_graph.nodes
    grids = np.full(
        (len(SLICE_BEEF_STATES), len(location_states), len(key_states)),
        np.nan,
    )

    for beef_index, beef in enumerate(SLICE_BEEF_STATES):
        for row, location in enumerate(location_states):
            for col, key in enumerate(key_states):
                state = (location, key, beef)
                if state in reference_distances and state in coupled_distances:
                    grids[beef_index, row, col] = (
                        coupled_distances[state] - reference_distances[state]
                    )

    return grids


def plot_distance_delta_slices(config, coupled_config, file_name, title):
    """画一个 coupling anchor 相对 independent 的最短距离差值切片。"""
    reference_distances = distances_to_terminal(config)
    coupled_distances = distances_to_terminal(coupled_config)
    slice_grids = distance_delta_grids(
        reference_distances,
        coupled_distances,
        config,
    )

    if np.nanmin(slice_grids) < 0:
        raise ValueError("coupling 不应缩短到终点的最短距离")
    goal_state = config.terminal_predicate.goal_state
    if slice_grids[
        SLICE_BEEF_STATES.index(goal_state[2]),
        config.location_graph.nodes.index(goal_state[0]),
        config.key_graph.nodes.index(goal_state[1]),
    ] != 0:
        raise ValueError("终止状态的距离差值必须为 0")

    max_delta = np.nanmax(slice_grids)
    vmax = max(1, max_delta)
    color_map = matplotlib.colormaps["YlOrRd"].copy()
    color_map.set_bad("#D9D9D9")
    location_states = config.location_graph.nodes
    key_states = config.key_graph.nodes

    figure, axes = plt.subplots(
        1, 3, figsize=(15, 5.6), layout="constrained",
    )
    for axis, beef, grid in zip(axes, SLICE_BEEF_STATES, slice_grids):
        image = axis.imshow(grid, cmap=color_map, vmin=0, vmax=vmax)
        for row in range(len(location_states)):
            for col in range(len(key_states)):
                text = "x" if np.isnan(grid[row, col]) else str(int(grid[row, col]))
                color = "#777777" if np.isnan(grid[row, col]) else "#222222"
                axis.text(
                    col,
                    row,
                    text,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color=color,
                )

        axis.set_title(f"beef = {config.beef_graph.labels[beef]} {beef}")
        axis.set_xticks(range(len(key_states)))
        axis.set_xticklabels(
            [config.key_graph.labels[state] for state in key_states],
            rotation=90,
            fontsize=6,
        )
        axis.set_yticks(range(len(location_states)))
        axis.set_yticklabels([str(state) for state in location_states], fontsize=6)
        axis.set_xlabel("Key state (head/tail)")
        axis.set_ylabel("Location state (row, col)")

    colorbar = figure.colorbar(
        image,
        ax=axes,
        shrink=0.85,
        label="extra optimal steps",
    )
    if max_delta == 0:
        colorbar.set_ticks([0])
    figure.suptitle(title, fontsize=13)
    save_figure(figure, file_name)


# 5. 图五：四个 anchors 的对比


def plot_range_panel(axis, results, metric_name, series, colors, y_label):
    """画带上下界的 range 图；上下界相同时用标记和文字标出数值。"""
    anchor_count = len(results)
    x_positions = np.arange(anchor_count)

    for index, (key, label) in enumerate(series):
        offset = (index - (len(series) - 1) / 2) * 0.25
        positions = x_positions + offset
        color = colors[index]
        for anchor_index, result in enumerate(results):
            if key is None:
                # switch_range 本身就是 [low, high] 列表。
                low, high = result[metric_name]
            else:
                low, high = result[metric_name][key]
            axis.plot(
                [positions[anchor_index], positions[anchor_index]],
                [low, high],
                color=color,
                linewidth=2,
            )
            axis.plot(
                positions[anchor_index],
                low,
                "o",
                color=color,
                clip_on=False,
            )
            if high != low:
                axis.plot(
                    positions[anchor_index],
                    high,
                    "o",
                    color=color,
                    clip_on=False,
                )
            axis.annotate(
                f"[{low}, {high}]",
                (positions[anchor_index], high),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=6.5,
                color=color,
            )
        # 用空线条生成图例项。
        axis.plot([], [], color=color, linewidth=2, label=label)

    axis.set_xticks(x_positions)
    axis.set_xticklabels(
        [result["anchor"] for result in results],
        rotation=20,
        ha="right",
        fontsize=8,
    )
    axis.set_ylabel(y_label)
    axis.legend(fontsize=7, loc="upper left")
    axis.grid(axis="y", alpha=0.3)


def plot_anchor_comparison(results):
    """用 2x2 布局对比四个 anchors 的 S/K、N、D 和 L*。"""
    x_positions = np.arange(len(results))
    anchor_names = [result["anchor"] for result in results]

    figure, axes = plt.subplots(2, 2, figsize=(12.5, 9))

    # 面板 1：两个活跃方向的 schema 数 S 与 grounded template 数 K。
    axis = axes[0, 0]
    bar_width = 0.2
    bar_series = (
        ("schema_coupling", "k_to_l", "$S_{K\\to L}$ (schemas)", "#1F77B4", "//"),
        ("template_coupling", "k_to_l", "$K_{K\\to L}$ (templates)", "#1F77B4", ""),
        ("schema_coupling", "l_to_b", "$S_{L\\to B}$ (schemas)", "#FF7F0E", "//"),
        ("template_coupling", "l_to_b", "$K_{L\\to B}$ (templates)", "#FF7F0E", ""),
    )
    for index, (field, key, label, color, hatch) in enumerate(bar_series):
        offsets = x_positions + (index - 1.5) * bar_width
        counts = [result[field][key] for result in results]
        axis.bar(
            offsets,
            counts,
            width=bar_width,
            color=color,
            hatch=hatch,
            edgecolor="white",
            label=label,
        )
        for position, count in zip(offsets, counts):
            axis.text(
                position,
                count + 0.15,
                str(count),
                ha="center",
                va="bottom",
                fontsize=6.5,
            )
    axis.set_xticks(x_positions)
    axis.set_xticklabels(anchor_names, rotation=20, ha="right", fontsize=8)
    axis.set_ylabel("count")
    axis.set_ylim(0, 14)
    axis.legend(fontsize=7)
    axis.grid(axis="y", alpha=0.3)
    axis.set_title("Coupling counts: schemas (S) vs grounded templates (K)")

    # 面板 2：最优路径上的耦合模板使用范围 N。
    axis = axes[0, 1]
    plot_range_panel(
        axis,
        results,
        "path_coupling_range",
        (
            ("k_to_l", "$N_{K\\to L}$"),
            ("l_to_b", "$N_{L\\to B}$"),
        ),
        ("#1F77B4", "#FF7F0E"),
        "coupled template uses per optimal path",
    )
    axis.set_ylim(-0.5, 5.5)
    axis.set_title("Coupled-template range $N$ along optimal paths")

    # 面板 3：动作域切换范围 D。
    axis = axes[1, 0]
    plot_range_panel(
        axis,
        results,
        "switch_range",
        ((None, "$D$"),),
        ("#2CA02C",),
        "action-domain switches per optimal path",
    )
    axis.set_ylim(0, 11)
    axis.set_title("Action-domain switch range $D$ along optimal paths")

    # 面板 4：最优原语长度 L*。
    axis = axes[1, 1]
    lengths = [result["optimal_length"] for result in results]
    axis.bar(x_positions, lengths, width=0.5, color="#9467BD")
    for position, length in zip(x_positions, lengths):
        axis.text(
            position,
            length + 0.15,
            str(length),
            ha="center",
            va="bottom",
            fontsize=8,
        )
    axis.set_xticks(x_positions)
    axis.set_xticklabels(anchor_names, rotation=20, ha="right", fontsize=8)
    axis.set_ylabel("steps")
    axis.set_ylim(0, 12)
    axis.grid(axis="y", alpha=0.3)
    axis.set_title("Optimal primitive length $L^*$")

    figure.suptitle(
        "Four task anchors: coupling structure and optimal-path metrics",
        fontsize=14,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(figure, "week3_anchor_comparison")


def main():
    """按固定顺序生成全部展示图。"""
    setup_style()
    FIGURES_DIR.mkdir(exist_ok=True)

    # 图一和图二都使用 combined anchor。
    plot_three_factor_graphs(COMBINED_CONFIG)
    plot_value_slices(COMBINED_CONFIG)

    # 这两张图固定同一个联合状态，显示加入单个 coupling 后多出的步数。
    independent_config = TASK_CONFIGS["independent"]
    plot_distance_delta_slices(
        independent_config,
        TASK_CONFIGS["key_gates_location"],
        "week3_key_gate_distance_delta",
        "Key gate: d*(key-gates-location) - d*(independent)",
    )
    plot_distance_delta_slices(
        independent_config,
        TASK_CONFIGS["location_gates_beef"],
        "week3_location_beef_distance_delta",
        "Location beef gates: d*(location-gates-beef) - d*(independent)",
    )

    # 图五：四个 anchors 各分析一次，结果只计算一次并复用。
    results = []
    for config in TASK_CONFIGS.values():
        print(f"analyzing anchor: {config.task_name}")
        results.append(analyze_task(config))
    plot_anchor_comparison(results)


if __name__ == "__main__":
    main()
