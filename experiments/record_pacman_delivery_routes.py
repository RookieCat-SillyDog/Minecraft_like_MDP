"""从主实验最终模型记录路线
"""

import argparse
import json
import pickle
import random
from pathlib import Path

from src.algorithms.q_learning import select_action
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine
from src.tasks.pacman_delivery import DeliveryTask, goals


def evaluate_low_goals(task, Q_low, seed, config, n_episodes, training_step):
    # 单独检查导航：从起点和其他地标出发，到达所选目标就结束。
    rng = random.Random(seed)
    eval_low = dict(Q_low)  # 缺失行只添加到副本，不修改训练表。
    starts = [task.env.start] + [
        position for position in task.env.positions if task.env.label(position)
    ]
    rows = []
    for goal in goals:
        successes = total_steps = episodes = 0
        for start in starts:
            if goal in task.env.label(start):
                continue  # 已经在目标上的情况不计入导航成绩。
            for _ in range(n_episodes):
                state = (start, task.rm.initial_state)
                reached = terminal = False
                steps = 0
                while not reached and not terminal and steps < config.max_episode_steps:
                    low_key = (state[0], goal)
                    if low_key not in eval_low:
                        eval_low[low_key] = {action: 0.0 for action in task.actions}
                    action = select_action(eval_low, low_key, 0.0, task.actions, rng)
                    state, _, _, reached, terminal = task.step(state, goal, action)
                    steps += 1
                episodes += 1
                successes += reached
                total_steps += steps if reached else config.max_episode_steps
        rows.append({
            "seed": seed, "step": training_step, "goal": goal,
            "eval_episodes": episodes, "success_rate": successes / episodes,
            "mean_steps": total_steps / episodes,
        })
    return rows


def record_routes(task, algorithm, Q, seed, Q_high=None, n_episodes=10, max_steps=300):
    # 训练后另做贪心评估；独立随机数和Q表副本，不影响训练或原评估曲线。
    rng = random.Random(seed)
    eval_Q = dict(Q)
    eval_high = dict(Q_high) if Q_high is not None else {}
    episodes = []
    for episode in range(n_episodes):
        state = task.reset()
        goal = None
        option_count = 0
        route = []
        while not task.is_success(state) and len(route) < max_steps:
            if algorithm == "tabular_hdqn":
                if goal is None:
                    candidates = task.legal_goals(state)
                    if state not in eval_high:
                        eval_high[state] = {candidate: 0.0 for candidate in candidates}
                    goal = select_action(eval_high, state, 0.0, candidates, rng)
                    option_count += 1
                low_key = (task.low_state(state), goal)
                if low_key not in eval_Q:
                    eval_Q[low_key] = {action: 0.0 for action in task.actions}
                action = select_action(eval_Q, low_key, 0.0, task.actions, rng)
            else:
                # 与QRM的evaluate一致：只随机打破最优动作并列。
                values = eval_Q[state]
                best = [action for action in task.actions
                        if values[action] == max(values.values())]
                action = rng.choice(best)
            next_state, reward, _, reached, _ = task.step(state, goal, action)
            route.append({
                "step": len(route) + 1,
                "option": option_count if algorithm == "tabular_hdqn" else None,
                "goal": goal,
                "position": state[0], "action": action,
                "next_position": next_state[0],
                "rm_state": state[1], "next_rm_state": next_state[1],
                "labels": sorted(task.env.label(next_state[0])),
                "goal_reached": reached if algorithm == "tabular_hdqn" else None,
                "external_reward": reward,
            })
            state = next_state
            if reached:
                goal = None
        episodes.append({
            "algorithm": algorithm, "seed": seed, "episode": episode + 1,
            "success": task.is_success(state), "primitive_steps": len(route),
            "option_count": option_count if algorithm == "tabular_hdqn" else None,
            "route": route,
        })
    return episodes


def main():
    parser = argparse.ArgumentParser(description="读取最终Q表，单独记录h-DQN和QRM路线")
    parser.add_argument("model_path", type=Path)
    args = parser.parse_args()
    with args.model_path.open("rb") as file:
        saved = pickle.load(file)
    settings = saved["settings"]
    task = DeliveryTask(OfficeWorld(settings["map"]), RewardMachine(settings["reward_machine"]))
    episodes = []
    for model in saved["models"]:
        episodes.extend(record_routes(
            task, "tabular_hdqn", model["Q_low"], model["seed"], model["Q_high"],
            settings["eval_episodes"], settings["hdqn"]["max_episode_steps"]))
        episodes.extend(record_routes(
            task, "qrm", model["Q_qrm"], model["seed"],
            n_episodes=settings["eval_episodes"], max_steps=settings["hdqn"]["max_episode_steps"]))
    prefix = args.model_path.stem.removesuffix("_models")
    route_path = args.model_path.with_name(prefix + "_routes.json")
    route_path.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Routes: {route_path}", flush=True)


if __name__ == "__main__":
    main()
