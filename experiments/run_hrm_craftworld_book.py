"""在 Book 任务上对比三种算法：Q-learning、QRM、表格型 h-DQN。"""

import csv
import random

import matplotlib.pyplot as plt
import numpy as np

from src.algorithms.tabular_hdqn import (
    TabularHDQNConfig,
    evaluate_tabular_hdqn,
    train_tabular_hdqn,
)
from src.algorithms.q_learning import train_q_learning
from src.algorithms.qrm import train_qrm
from src.config import (
    REPOSITORY_ROOT,
    load_hrm_craftworld_config,
    load_reward_machine_config,
)
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine

task_name = "hrm_craftworld_book"
filename = f"{task_name}_tabular_hdqn"
seeds = range(5)
n_interactions = 50000
eval_every = 1000
eval_episodes = 20
gamma = 0.99
flat_max_steps = 200
config = TabularHDQNConfig(
    gamma=gamma,
    alpha_low=0.1,
    alpha_high=0.1,
    pretrain_interactions=0,  # 50k总预算全部用于联合训练。
    max_episode_steps=flat_max_steps,
)

# 图中每条线的颜色和方法标签。
method_styles = {
    "q_learning": ("Q-learning", "#0072B2"),
    "qrm": ("QRM", "#D55E00"),
    "tabular_hdqn": ("Tabular h-DQN", "#009E73"),
}


class BookTask:
    """Book 任务适配：高层状态为 (position, rm_state)，低层只使用 position。"""

    actions = OfficeWorld.actions
    goals = ("sugarcane", "rabbit", "workbench", "table")

    def __init__(self, env, rm):
        self.env = env
        self.rm = rm

    def reset(self):
        return (self.env.start, self.rm.initial_state)

    def legal_goals(self, state):
        position, _ = state
        current_labels = self.env.label(position)
        return tuple(goal for goal in self.goals if goal not in current_labels)

    def low_state(self, state):
        return state[0]

    def low_goal_rewards(self, state, next_state):
        # 一次移动为多个目标生成导航经验；脚下已满足的目标不重复写入。
        labels = self.env.label(next_state[0])
        rewards = []
        for goal in self.legal_goals(state):
            reached = goal in labels
            rewards.append((goal, float(reached), reached))
        return rewards

    def step(self, state, goal, action):
        position, rm_state = state
        next_position = self.env.next_position(position, action)
        labels = self.env.label(next_position)
        next_rm_state, external_reward = self.rm.next_state(rm_state, labels)
        goal_reached = goal in labels
        intrinsic_reward = 1.0 if goal_reached else 0.0
        environment_terminal = self.rm.is_terminal(next_rm_state)
        return (
            (next_position, next_rm_state),
            external_reward,
            intrinsic_reward,
            goal_reached,
            environment_terminal,
        )

    def is_success(self, state):
        return self.rm.is_terminal(state[1])


def make_row(method, seed, step, stats):
    # 层级评估叫 mean_primitive_steps，flat 评估叫 mean_steps。
    if method == "tabular_hdqn":
        mean_steps = stats["mean_primitive_steps"]
    else:
        mean_steps = stats["mean_steps"]
    return {
        "task": task_name,
        "method": method,
        "seed": seed,
        "step": step,
        "success_rate": stats["success_rate"],
        "mean_return": stats["mean_return"],
        "mean_primitive_steps": mean_steps,
        "mean_option_count": stats.get("mean_option_count", ""),
    }


def run_hdqn_seed(task, seed):
    """单种子：step=0 只读基线 + 训练内评估点。"""
    baseline = evaluate_tabular_hdqn(
        task, {}, {}, config, eval_episodes, random.Random(seed)
    )
    rows = [make_row("tabular_hdqn", seed, 0, baseline)]
    _, _, log = train_tabular_hdqn(
        task,
        config,
        n_interactions,
        eval_every=eval_every,
        eval_episodes=eval_episodes,
        seed=seed,
    )
    rows.extend(
        make_row("tabular_hdqn", seed, stats["step"], stats)
        for stats in log
    )
    return rows


def run_flat_seed(method, train, env, rm, seed):
    """单种子 flat 训练；评估点由训练循环按 eval_every 触发。"""
    _, log = train(
        env,
        rm,
        env.start,
        n_interactions,
        eval_every=eval_every,
        eval_episodes=eval_episodes,
        max_steps=flat_max_steps,
        gamma=gamma,
        seed=seed,
    )
    return [make_row(method, seed, stats["step"], stats) for stats in log]


def draw_learning_curve(rows):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for method, (label, color) in method_styles.items():
        method_rows = [row for row in rows if row["method"] == method]
        if not method_rows:
            continue
        # 各方法用自己的评估点（层级有 step=0 基线，flat 没有）。
        steps = sorted({row["step"] for row in method_rows})
        means = []
        stds = []
        for step in steps:
            rates = [
                row["success_rate"]
                for row in method_rows
                if row["step"] == step
            ]
            means.append(np.mean(rates))
            stds.append(np.std(rates))
        means = np.array(means)
        stds = np.array(stds)
        ax.plot(steps, means, label=label, color=color, linewidth=1.8)
        ax.fill_between(steps, means - stds, means + stds, alpha=0.2,
                        color=color)
    ax.set_xlabel("Environment interactions")
    ax.set_ylabel("Evaluation success rate")
    ax.set_title(f"{task_name}: three methods ({len(seeds)} seeds)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(0, n_interactions)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    output_dir = REPOSITORY_ROOT / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename}_learning_curve.svg"
    fig.savefig(output_path)
    fig.savefig(output_path.with_suffix(".png"), dpi=120)
    plt.close(fig)
    return output_path


def main():
    env = OfficeWorld(load_hrm_craftworld_config())
    rm = RewardMachine(load_reward_machine_config(task_name))
    task = BookTask(env, rm)
    flat_methods = (
        ("q_learning", train_q_learning),
        ("qrm", train_qrm),
    )

    results = []
    for method, train in flat_methods:
        final_rates = []
        for seed in seeds:
            rows = run_flat_seed(method, train, env, rm, seed)
            results.extend(rows)
            final_rates.append(rows[-1]["success_rate"])
        print(f"{method}: mean final success = {np.mean(final_rates):.3f}")
    final_rates = []
    for seed in seeds:
        results.extend(run_hdqn_seed(task, seed))
        final_rates.append(results[-1]["success_rate"])
    print("tabular_hdqn: mean final success = "
          f"{np.mean(final_rates):.3f}")

    csv_path = (
        REPOSITORY_ROOT
        / "experiments"
        / "results"
        / f"{filename}_learning_curves.csv"
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task", "method", "seed", "step", "success_rate", "mean_return",
        "mean_primitive_steps", "mean_option_count",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"  -> {csv_path} ({len(results)} rows)")

    output_path = draw_learning_curve(results)
    print(f"  -> {output_path}")


if __name__ == "__main__":
    main()
