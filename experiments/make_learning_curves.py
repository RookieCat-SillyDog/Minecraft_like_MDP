"""生成 Q-learning vs QRM 学习曲线（10 种子 × 2 任务 × 2 方法）。
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

from src.algorithms.q_learning import train_q_learning
from src.algorithms.qrm import train_qrm
from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine

TASK_SETTINGS = {
    "coffee_office": {
        "n_interactions": 2000,
        "eval_every": 100,
        "max_steps": 50,
    },
    "visit_abcd": {
        "n_interactions": 10000,
        "eval_every": 500,
        "max_steps": 200,
    },
}
METHODS = {
    "Q-learning": train_q_learning,
    "QRM": train_qrm,
}


def run_task(task, settings):
    env = OfficeWorld(load_officeworld_config())
    rm = RewardMachine(load_reward_machine_config(task))
    rows = []
    success_rates = {method: {} for method in METHODS}
    for seed in range(10):
        for method, train in METHODS.items():
            _, log = train(
                env,
                rm,
                env.start,
                n_interactions=settings["n_interactions"],
                eval_every=settings["eval_every"],
                eval_episodes=20,
                max_steps=settings["max_steps"],
                gamma=0.99,
                alpha=0.1,
                epsilon=0.1,
                seed=seed,
                q_init=0.0,
            )
            for stats in log:
                step = stats["step"]
                rows.append([
                    task,
                    method,
                    seed,
                    step,
                    stats["success_rate"],
                    stats["mean_return"],
                    stats["mean_steps"],
                ])
                if step not in success_rates[method]:
                    success_rates[method][step] = []
                success_rates[method][step].append(stats["success_rate"])
    return rows, success_rates


def draw_learning_curve(success_rates, task, max_interactions):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    colors = {"Q-learning": "#1f77b4", "QRM": "#d62728"}
    for method in METHODS:
        steps = sorted(success_rates[method])
        means = np.array([
            np.mean(success_rates[method][step]) for step in steps
        ])
        stds = np.array([
            np.std(success_rates[method][step]) for step in steps
        ])
        ax.plot(steps, means, label=method, color=colors[method], linewidth=1.8)
        ax.fill_between(
            steps, means - stds, means + stds,
            alpha=0.2, color=colors[method],
        )
    ax.set_xlabel("Environment interactions")
    ax.set_ylabel("Evaluation success rate")
    ax.set_title(f"{task}: Q-learning vs QRM (10 seeds)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(0, max_interactions)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    output_dir = ROOT / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"learning_curves_{task}.svg"
    fig.savefig(output_path)
    fig.savefig(output_path.with_suffix(".png"), dpi=120)
    plt.close(fig)
    return output_path


def main():
    all_rows = []
    for task, settings in TASK_SETTINGS.items():
        rows, success_rates = run_task(task, settings)
        all_rows.extend(rows)
        output_path = draw_learning_curve(
            success_rates, task, settings["n_interactions"]
        )
        for method in METHODS:
            final_step = max(success_rates[method])
            final = np.mean(success_rates[method][final_step])
            print(f"  {task:14s} {method:11s} final={final:.3f}")
        print(f"  -> {output_path}")

    results_dir = ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = results_dir / "learning_curves.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "task", "method", "seed", "step", "success_rate",
            "mean_return", "mean_steps",
        ])
        writer.writerows(all_rows)
    print(f"\nRaw data: {csv_path} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
