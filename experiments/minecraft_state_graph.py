"""绘制 Day 8 的部分状态转移图。"""

from pathlib import Path
from math import hypot

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, Rectangle


FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"
MINI_GRID_SIZE = 1.5


def make_partial_graph_data(env):
    """通过环境接口计算图中需要展示的关键转移。"""
    examples = {
        "movement": [
            ("向右移动", env.initial_state, env.RIGHT),
            ("向下移动", env.initial_state, env.DOWN),
        ],
        "resources": [
            ("先收集 wood", (0, 3, 0, 0, 0), env.RIGHT),
            ("已有 iron 后收集 wood", (0, 3, 0, 1, 0), env.RIGHT),
            ("先收集 iron", (3, 0, 0, 0, 0), env.DOWN),
            ("已有 wood 后收集 iron", (3, 0, 1, 0, 0), env.DOWN),
        ],
        "factory": [
            ("资源不足", (4, 3, 1, 0, 0), env.RIGHT),
            ("资源齐全", (4, 3, 1, 1, 0), env.RIGHT),
        ],
    }

    graph_data = {}

    for group_name, group_examples in examples.items():
        graph_data[group_name] = []

        for description, state, action in group_examples:
            outcomes = env.transitions(state, action)

            if len(outcomes) != 1 or outcomes[0][0] != 1.0:
                raise ValueError("当前状态图只适用于确定性转移")

            next_state = outcomes[0][1]
            graph_data[group_name].append(
                (description, state, action, next_state)
            )

    return graph_data


def state_color(state):
    """根据资源和任务进度选择节点颜色。"""
    _, _, wood, iron, bridge = state

    if bridge:
        return "#D55E00"
    if wood and iron:
        return "#E69F00"
    if wood:
        return "#009E73"
    if iron:
        return "#56B4E9"

    return "#D9D9D9"


def draw_grid_state(axis, env, position, state):
    """用一个真实的 5x5 小地图展示状态。"""
    center_x, center_y = position
    agent_row, agent_col, wood, iron, bridge = state
    cell_size = MINI_GRID_SIZE / env.grid_size
    left = center_x - MINI_GRID_SIZE / 2
    top = center_y + MINI_GRID_SIZE / 2

    special_cells = {
        env.start: ("S", "#EEEEEE"),
        env.wood: ("W", "#D9F2E6"),
        env.iron: ("I", "#DDEFF8"),
        env.factory: ("F", "#FBE6CE"),
    }

    for row in range(env.grid_size):
        for col in range(env.grid_size):
            cell_left = left + col * cell_size
            cell_bottom = top - (row + 1) * cell_size
            symbol, background = special_cells.get(
                (row, col),
                ("", "#FFFFFF"),
            )

            axis.add_patch(Rectangle(
                (cell_left, cell_bottom),
                cell_size,
                cell_size,
                facecolor=background,
                edgecolor="#999999",
                linewidth=0.7,
            ))

            if symbol:
                axis.text(
                    cell_left + cell_size * 0.18,
                    cell_bottom + cell_size * 0.78,
                    symbol,
                    ha="center",
                    va="center",
                    fontsize=5.5,
                    color="#555555",
                )

    agent_x = left + (agent_col + 0.5) * cell_size
    agent_y = top - (agent_row + 0.5) * cell_size
    axis.add_patch(Circle(
        (agent_x, agent_y),
        radius=cell_size * 0.31,
        facecolor=state_color(state),
        edgecolor="#222222",
        linewidth=0.8,
        zorder=3,
    ))
    axis.text(
        agent_x,
        agent_y,
        "A",
        ha="center",
        va="center",
        fontsize=5.5,
        fontweight="bold",
        zorder=4,
    )
    axis.text(
        center_x,
        top - MINI_GRID_SIZE - 0.16,
        f"s=({agent_row},{agent_col},{wood},{iron},{bridge})",
        ha="center",
        va="top",
        fontsize=8,
    )


def draw_transition(axis, start, end, action_name):
    """绘制一条带动作名称的有向边。"""
    start_x, start_y = start
    end_x, end_y = end
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    distance = hypot(delta_x, delta_y)
    unit_x = delta_x / distance
    unit_y = delta_y / distance

    # 把箭头端点放在小地图边缘，避免箭头穿过地图。
    edge_distance = (
        MINI_GRID_SIZE
        / 2
        / max(abs(unit_x), abs(unit_y))
        + 0.08
    )
    arrow_start = (
        start_x + unit_x * edge_distance,
        start_y + unit_y * edge_distance,
    )
    arrow_end = (
        end_x - unit_x * edge_distance,
        end_y - unit_y * edge_distance,
    )

    axis.annotate(
        "",
        xy=arrow_end,
        xytext=arrow_start,
        arrowprops={
            "arrowstyle": "->",
            "color": "#333333",
            "linewidth": 1.4,
        },
    )
    axis.text(
        (start_x + end_x) / 2,
        (start_y + end_y) / 2 + 0.18,
        action_name,
        ha="center",
        fontsize=9,
    )


def prepare_axis(axis, title, x_limits, y_limits):
    """设置一个局部状态图面板。"""
    axis.set_title(title, loc="left", fontsize=12)
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.axis("off")


def draw_movement_panel(axis, env, transitions):
    """展示同一状态执行不同动作产生的分支。"""
    start_position = (-3.4, 0.0)
    target_positions = [(3.0, 1.4), (3.0, -1.4)]
    start_state = transitions[0][1]

    draw_grid_state(axis, env, start_position, start_state)

    for transition, target_position in zip(
        transitions,
        target_positions,
    ):
        _, _, action, next_state = transition
        draw_grid_state(axis, env, target_position, next_state)
        draw_transition(
            axis,
            start_position,
            target_position,
            env.ACTION_NAMES[action],
        )

    prepare_axis(
        axis,
        "A. 同一状态的动作分支",
        (-5.0, 5.0),
        (-2.5, 2.5),
    )


def draw_resource_panel(axis, env, transitions):
    """展示 wood 和 iron 可以按任意顺序收集。"""
    positions = [
        ((-5.3, 1.6), (-2.1, 1.6)),
        ((-5.3, -1.7), (-2.1, -1.7)),
        ((2.0, 1.6), (5.2, 1.6)),
        ((2.0, -1.7), (5.2, -1.7)),
    ]

    axis.text(-3.7, 2.75, "进入 wood", ha="center", fontsize=10)
    axis.text(3.6, 2.75, "进入 iron", ha="center", fontsize=10)

    for transition, (start, end) in zip(transitions, positions):
        _, state, action, next_state = transition
        draw_grid_state(axis, env, start, state)
        draw_grid_state(axis, env, end, next_state)
        draw_transition(
            axis,
            start,
            end,
            env.ACTION_NAMES[action],
        )

    prepare_axis(
        axis,
        "B. 进入资源格时，位置和资源标志一起变化",
        (-7.0, 7.0),
        (-3.0, 3.2),
    )


def draw_factory_panel(axis, env, transitions):
    """对比资源不足和资源齐全时进入 factory 的结果。"""
    positions = [
        ((-2.4, 1.6), (2.4, 1.6)),
        ((-2.4, -1.6), (2.4, -1.6)),
    ]

    for transition, (start, end) in zip(transitions, positions):
        description, state, action, next_state = transition
        draw_grid_state(axis, env, start, state)
        draw_grid_state(axis, env, end, next_state)
        draw_transition(
            axis,
            start,
            end,
            env.ACTION_NAMES[action],
        )
        axis.text(
            -4.8,
            start[1],
            description,
            ha="left",
            va="center",
            fontsize=10,
        )

    axis.text(
        4.2,
        -1.0,
        "终止状态",
        ha="center",
        va="center",
        fontsize=10,
        color="#A43F00",
    )
    prepare_axis(
        axis,
        "C. 进入 factory 后是否完成 bridge 取决于资源状态",
        (-5.5, 5.5),
        (-2.8, 2.8),
    )


def save_partial_state_graph(env):
    """生成包含分支和关键状态更新的部分状态转移图。"""
    plt.rcParams.update({
        "font.sans-serif": [
            "Microsoft YaHei",
            "SimHei",
            "DejaVu Sans",
        ],
        "axes.unicode_minus": False,
    })

    graph_data = make_partial_graph_data(env)
    figure, axes = plt.subplots(
        3,
        1,
        figsize=(16, 16),
        gridspec_kw={"height_ratios": [1.0, 1.35, 1.15]},
    )

    draw_movement_panel(axes[0], env, graph_data["movement"])
    draw_resource_panel(axes[1], env, graph_data["resources"])
    draw_factory_panel(axes[2], env, graph_data["factory"])

    legend = [
        Patch(facecolor="#D9D9D9", label="Agent：尚未收集资源"),
        Patch(facecolor="#009E73", label="Agent：仅有 wood"),
        Patch(facecolor="#56B4E9", label="Agent：仅有 iron"),
        Patch(facecolor="#E69F00", label="Agent：wood 与 iron 齐全"),
        Patch(facecolor="#D55E00", label="Agent：bridge 完成（终止）"),
    ]
    figure.legend(
        handles=legend,
        loc="lower center",
        frameon=False,
        ncol=5,
    )
    figure.suptitle(
        "Day 8 Minecraft-like MDP 部分状态转移图",
        fontsize=15,
    )
    figure.text(
        0.5,
        0.035,
        "S/W/I/F 表示起点、wood、iron、factory；A 表示 Agent；"
        "状态格式为 (row, col, wood, iron, bridge)",
        ha="center",
        fontsize=10,
    )
    figure.tight_layout(rect=(0.02, 0.08, 0.98, 0.96))

    FIGURES_DIR.mkdir(exist_ok=True)
    png_path = FIGURES_DIR / "day08_partial_state_graph.png"
    svg_path = FIGURES_DIR / "day08_partial_state_graph.svg"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight")
    plt.close(figure)

    return png_path, svg_path
