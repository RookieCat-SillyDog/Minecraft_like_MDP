# 固定 Delivery 地图上的表格型 h-DQN 与 QRM 对照。

import csv
import json
import pickle
import random
from dataclasses import asdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.algorithms.q_learning import evaluate, init_Q
from src.algorithms.qrm import train_qrm
from src.algorithms.tabular_hdqn import (
    TabularHDQNConfig,
    evaluate_tabular_hdqn,
    train_tabular_hdqn,
)
from src.config import (
    REPOSITORY_ROOT,
    load_pacman_delivery_config,
    load_reward_machine_config,
)
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine
from src.tasks.pacman_delivery import DeliveryTask


seeds = [5]
hdqn_config = TabularHDQNConfig()
joint_training_interactions = 150000  # 加上5万步预训练，总预算为20万步。
total_interactions = hdqn_config.pretrain_interactions + joint_training_interactions
eval_every = 1000
eval_episodes = 10
qrm_epsilon = 0.1
qrm_train_max_episode_steps = 1000  # QRM训练回合延长，评估仍限300步。

result_dir = REPOSITORY_ROOT / "experiments" / "results"
figure_dir = REPOSITORY_ROOT / "figures"
filename = "pacman_delivery_hdqn_vs_qrm_seed5_200k_all_goals_navigation_bootstrap_pretrain1000_qrm_train1000_duration_discount"


def draw_learning_curves(rows):
    # 单种子直接画评估曲线；多个种子时画均值和±1样本标准差，不平滑。
    figure_dir.mkdir(parents=True, exist_ok=True)
    steps = sorted({row["step"] for row in rows})
    for metric, ylabel, suffix in (
        ("success_rate", "Evaluation success rate", "success"),
        ("mean_primitive_steps", "Evaluation primitive steps", "steps"),
    ):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for algorithm, label, color in (
            ("tabular_hdqn", "Tabular h-DQN", "#EE7733"),
            ("qrm", "QRM", "#0077BB"),
        ):
            values = []
            for seed in seeds:
                values.append([
                    row[metric] for row in rows
                    if row["algorithm"] == algorithm and row["seed"] == seed
                ])
            values = np.array(values)
            mean = values.mean(axis=0)
            if metric == "success_rate":
                ax.set_ylim(-0.03, 1.03)
            ax.plot(steps, mean, label=label, color=color)
            if len(seeds) > 1:
                std = values.std(axis=0, ddof=1)
                lower, upper = mean - std, mean + std
                if metric == "success_rate":
                    lower, upper = np.clip(lower, 0, 1), np.clip(upper, 0, 1)
                ax.fill_between(steps, lower, upper, color=color, alpha=0.15)
        ax.axvline(hdqn_config.pretrain_interactions, color="gray", linestyle="--",
                   label="h-DQN joint training starts")
        ax.set(xlabel="Training environment interactions", ylabel=ylabel,
               xlim=(0, total_interactions))
        ax.set_title("Pacman Delivery: tabular h-DQN vs QRM", pad=34)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, fontsize=9)
        ax.grid(alpha=0.2)
        curve_description = f"Seed {seeds[0]}" if len(seeds) == 1 else "Mean ± 1 SD"
        fig.text(0.5, 0.01,
                 f"{curve_description}; failed episodes count as {hdqn_config.max_episode_steps} steps.",
                 ha="center", fontsize=8)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        for extension in ("png", "svg"):
            path = figure_dir / f"{filename}_{suffix}.{extension}"
            fig.savefig(path, dpi=200, bbox_inches="tight")
            print(f"Figure: {path}", flush=True)
        plt.close(fig)


def save_settings(map_config, rm_config):
    # 保存实际地图、RM和全部算法参数；评估与回放不计入交互预算。
    result_dir.mkdir(parents=True, exist_ok=True)
    settings = {
        "seeds": list(seeds),
        "training_interactions_per_algorithm_per_seed": total_interactions,
        "eval_every": eval_every,
        "eval_episodes": eval_episodes,
        "map": map_config,
        "reward_machine": rm_config,
        "hdqn": asdict(hdqn_config),
        "qrm": {
            "gamma": hdqn_config.gamma, "alpha": hdqn_config.alpha_low,
            "epsilon": qrm_epsilon, "q_init": 0.0,
            "train_max_episode_steps": qrm_train_max_episode_steps,
            "eval_max_episode_steps": hdqn_config.max_episode_steps,
        },
    }
    settings_path = result_dir / f"{filename}_settings.json"
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return settings


def format_learning_rows(algorithm, seed, baseline, log, steps_key):
    # 两种评估函数的步数字段不同，统一为曲线需要的五列。
    baseline["step"] = 0
    rows = []
    for stats in [baseline] + log:
        rows.append({
            "algorithm": algorithm, "seed": seed, "step": stats["step"],
            "success_rate": stats["success_rate"],
            "mean_primitive_steps": stats[steps_key],
        })
    return rows


def run_hdqn(task, seed):
    print(f"seed={seed}: tabular_hdqn, {total_interactions:,} interactions", flush=True)
    baseline = evaluate_tabular_hdqn(
        task, {}, {}, hdqn_config, eval_episodes, random.Random(seed))
    Q_low, Q_high, log = train_tabular_hdqn(
        task, hdqn_config, total_interactions,
        eval_every=eval_every, eval_episodes=eval_episodes, seed=seed)
    rows = format_learning_rows(
        "tabular_hdqn", seed, baseline, log, "mean_primitive_steps")
    final = rows[-1]
    print(f"success={final['success_rate']:.2f}, steps={final['mean_primitive_steps']:.1f}",
          flush=True)
    return rows, {"Q_low": Q_low, "Q_high": Q_high}


def run_qrm(task, seed):
    env, rm = task.env, task.rm
    print(f"seed={seed}: qrm, {total_interactions:,} interactions", flush=True)
    baseline = evaluate(
        init_Q(env, rm), env, rm, env.start, eval_episodes,
        hdqn_config.max_episode_steps, hdqn_config.gamma, random.Random(seed))
    Q, log = train_qrm(
        env, rm, env.start, total_interactions,
        eval_every=eval_every, eval_episodes=eval_episodes,
        max_steps=qrm_train_max_episode_steps,
        eval_max_steps=hdqn_config.max_episode_steps, gamma=hdqn_config.gamma,
        alpha=hdqn_config.alpha_low, epsilon=qrm_epsilon, seed=seed, q_init=0.0)
    rows = format_learning_rows("qrm", seed, baseline, log, "mean_steps")
    final = rows[-1]
    print(f"success={final['success_rate']:.2f}, steps={final['mean_primitive_steps']:.1f}",
          flush=True)
    return rows, Q


def save_models(models, settings):
    # 独立路线入口读取这些最终Q表，无需重新训练。
    model_path = result_dir / f"{filename}_models.pkl"
    with model_path.open("wb") as file:
        pickle.dump({"settings": settings, "models": models}, file)
    print(f"Models: {model_path}", flush=True)


def main():
    map_config = load_pacman_delivery_config()
    rm_config = load_reward_machine_config("pacman_delivery")
    task = DeliveryTask(OfficeWorld(map_config), RewardMachine(rm_config))
    settings = save_settings(map_config, rm_config)
    rows = []
    models = []
    csv_path = result_dir / f"{filename}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "algorithm", "seed", "step", "success_rate", "mean_primitive_steps",
        ])
        writer.writeheader()
        for seed in seeds:
            hdqn_rows, model = run_hdqn(task, seed)
            writer.writerows(hdqn_rows)
            file.flush()  # 每方法完成后落盘，保留原先中断时已完成的数据。
            qrm_rows, Q_qrm = run_qrm(task, seed)
            writer.writerows(qrm_rows)
            file.flush()
            rows.extend(hdqn_rows)
            rows.extend(qrm_rows)
            model["seed"] = seed
            model["Q_qrm"] = Q_qrm
            models.append(model)
    save_models(models, settings)
    draw_learning_curves(rows)
    print(f"CSV: {csv_path}", flush=True)
    print(f"Settings: {result_dir / (filename + '_settings.json')}", flush=True)


if __name__ == "__main__":
    main()
