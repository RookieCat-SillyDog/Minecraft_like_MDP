import random
from collections import deque
from dataclasses import dataclass

from src.algorithms.q_learning import q_update, select_action


@dataclass(frozen=True)
class TabularHDQNConfig:
    gamma: float = 0.99  # 两层均按基础动作步数折扣。
    alpha_low: float = 0.1
    alpha_high: float = 0.1
    epsilon_end: float = 0.1  # 最终随机探索概率。
    anneal_steps: int = 50000  # 低层从预训练开始退火，高层从联合训练开始退火。
    success_window: int = 100  # 每个目标保留最近多少次执行结果。
    low_memory_size: int = 1000000
    high_memory_size: int = 50000
    batch_size: int = 64  # 每个基础步从两层经验池分别抽取的条数。
    pretrain_interactions: int = 50000  # 总预算中，只训练低层的基础步数。
    pretrain_max_episode_steps: int = 1000  # 只延长低层预训练的探索回合。
    max_episode_steps: int = 300  # 联合训练和评估的回合上限。


def _ensure_row(table, key, choices) -> None:
    if key not in table:
        table[key] = {choice: 0.0 for choice in choices}


def annealed_epsilon(steps: int, config: TabularHDQNConfig) -> float:
    # 调用方传入低层总训练步数或高层联合训练步数。
    remaining_fraction = max(0.0, 1.0 - steps / config.anneal_steps)
    return config.epsilon_end + (1.0 - config.epsilon_end) * remaining_fraction


def low_epsilon(goal_results, training_steps: int, config: TabularHDQNConfig) -> float:
    # goal_results 是当前目标的布尔窗口；True计为1，False计为0。
    window_full = len(goal_results) == config.success_window
    if window_full and sum(goal_results) / len(goal_results) > 0.9:
        return config.epsilon_end
    return annealed_epsilon(training_steps, config)


def _store_experience(memory, experience, write_index, capacity) -> int:
    # memory 是列表：未满时追加，满后循环覆盖旧记录，返回下次写入位置。
    if len(memory) < capacity:
        memory.append(experience)
    else:
        memory[write_index] = experience
    return (write_index + 1) % capacity


def replay_updates(Q_low, Q_high, low_memory, high_memory, config, rng) -> None:
    # 两个经验池分别抽样；直接修改 Q 表，不返回新表。
    # 低层经验：(状态键, 动作, 内在奖励, 下一状态键, 导航目标是否到达)。
    low_batch = rng.sample(low_memory, min(config.batch_size, len(low_memory)))
    for low_key, action, intrinsic_reward, next_low_key, goal_reached in low_batch:
        q_update(
            Q_low, low_key, action, intrinsic_reward, next_low_key,
            goal_reached, config.alpha_low, config.gamma)

    # 高层经验：(起始状态, 目标, 外在折扣回报, 持续步数, 结束状态, 后续目标, 回合是否结束)。
    high_batch = rng.sample(high_memory, min(config.batch_size, len(high_memory)))
    for (
        state,
        goal,
        option_return,
        duration,
        next_state,
        next_goals,
        episode_finished,
    ) in high_batch:
        target = option_return
        if not episode_finished:
            target += (config.gamma ** duration) * max(
                Q_high[next_state][next_goal] for next_goal in next_goals)
        Q_high[state][goal] += config.alpha_high * (target - Q_high[state][goal])


def evaluate_tabular_hdqn(task, Q_low, Q_high, config, eval_episodes, rng) -> dict:
    # ε=0，不更新 Q 值；并列最优仍随机选择。
    eval_low, eval_high = dict(Q_low), dict(Q_high)
    successes = total_steps = total_options = 0
    total_return = 0.0
    for _ in range(eval_episodes):
        state = task.reset()
        steps = 0
        environment_terminal = task.is_success(state)
        while not environment_terminal and steps < config.max_episode_steps:
            goals = task.legal_goals(state)
            _ensure_row(eval_high, state, goals)
            goal = select_action(eval_high, state, 0.0, goals, rng)
            total_options += 1
            goal_reached = False
            while (not goal_reached and not environment_terminal
                   and steps < config.max_episode_steps):
                low_key = (task.low_state(state), goal)
                _ensure_row(eval_low, low_key, task.actions)
                action = select_action(eval_low, low_key, 0.0, task.actions, rng)
                (state, external_reward, _, goal_reached,
                 environment_terminal) = task.step(state, goal, action)
                # 评估仍报告基础动作折扣回报，便于和旧实验比较。
                total_return += (config.gamma ** steps) * external_reward
                steps += 1
        successes += task.is_success(state)
        total_steps += steps
    return {
        "success_rate": successes / eval_episodes,
        "mean_return": total_return / eval_episodes,
        "mean_primitive_steps": total_steps / eval_episodes,
        "mean_option_count": total_options / eval_episodes,
    }


def train_tabular_hdqn(task, config, n_interactions, eval_every=1000,
                       eval_episodes=10, seed=0) -> tuple:
    # n_interactions 是包含预训练的基础步预算；返回两张 Q 表和评估日志列表。
    train_rng = random.Random(seed)
    replay_rng = random.Random(seed)
    eval_rng = random.Random(seed)
    Q_low, Q_high = {}, {}
    low_memory, high_memory = [], []
    low_write_index = high_write_index = 0
    goal_history = {}  # 字典：goal -> 最近若干次执行结果的 deque。
    training_steps = 0
    log = []

    # 外层开始新回合，中层选择目标，内层执行该目标的移动动作。
    while training_steps < n_interactions:
        state = task.reset()
        episode_steps = 0
        environment_terminal = task.is_success(state)
        pretraining = training_steps < config.pretrain_interactions
        episode_limit = config.max_episode_steps
        if pretraining:
            episode_limit = config.pretrain_max_episode_steps
        while not environment_terminal and episode_steps < episode_limit:
            goals = task.legal_goals(state)
            # 预训练随机选目标，只训练低层；联合阶段才学习高层。
            if pretraining:
                goal = train_rng.choice(goals)
            else:
                joint_steps = training_steps - config.pretrain_interactions
                _ensure_row(Q_high, state, goals)
                goal = select_action(
                    Q_high, state, annealed_epsilon(joint_steps, config), goals,
                    train_rng)
            if goal not in goal_history:
                goal_history[goal] = deque(maxlen=config.success_window)
            goal_results = goal_history[goal]
            option_start_state = state
            option_return = 0.0
            option_steps = 0

            while True:
                low_key = (task.low_state(state), goal)
                _ensure_row(Q_low, low_key, task.actions)
                action = select_action(
                    Q_low, low_key, low_epsilon(goal_results, training_steps, config),
                    task.actions, train_rng)
                (next_state, external_reward, _,
                 goal_reached, environment_terminal) = task.step(state, goal, action)
                training_steps += 1
                episode_steps += 1
                option_return += (config.gamma ** option_steps) * external_reward
                option_steps += 1
                # 环境终止或到回合上限时结束回合；到达目标也会结束当前 Option。
                episode_finished = (
                    environment_terminal or episode_steps >= episode_limit)
                option_finished = goal_reached or episode_finished

                # 同一步移动为多个目标生成经验；地标和奖励规则由 task 提供。
                for replay_goal, reward, reached in task.low_goal_rewards(state, next_state):
                    replay_key = (task.low_state(state), replay_goal)
                    next_low_key = (task.low_state(next_state), replay_goal)
                    _ensure_row(Q_low, replay_key, task.actions)
                    if not reached:
                        _ensure_row(Q_low, next_low_key, task.actions)
                    # 即使RM完成或回合超时，未到达的导航目标仍保留bootstrap。
                    low_experience = (replay_key, action, reward, next_low_key, reached)
                    low_write_index = _store_experience(
                        low_memory, low_experience, low_write_index, config.low_memory_size)
                state = next_state

                if option_finished:
                    goal_results.append(goal_reached)

                if option_finished and not pretraining:
                    if episode_finished:
                        next_goals = ()
                    else:
                        next_goals = task.legal_goals(state)
                        _ensure_row(Q_high, state, next_goals)
                    high_experience = (
                        option_start_state,
                        goal,
                        option_return,
                        option_steps,
                        state,
                        next_goals,
                        episode_finished,
                    )
                    high_write_index = _store_experience(
                        high_memory, high_experience, high_write_index,
                        config.high_memory_size)

                # 每个基础步都回放两层已有经验；预训练的高层池为空。
                replay_updates(
                    Q_low, Q_high, low_memory, high_memory, config, replay_rng)
                if training_steps % eval_every == 0:
                    stats = evaluate_tabular_hdqn(
                        task, Q_low, Q_high, config, eval_episodes, eval_rng)
                    stats["step"] = training_steps
                    log.append(stats)

                # 预算或预训练边界只截断采样；未完成的 Option 不算失败或高层经验。
                pretraining_finished = training_steps == config.pretrain_interactions
                budget_exhausted = training_steps >= n_interactions
                if option_finished or pretraining_finished or budget_exhausted:
                    break

            if episode_finished or pretraining_finished or budget_exhausted:
                break
    return Q_low, Q_high, log
