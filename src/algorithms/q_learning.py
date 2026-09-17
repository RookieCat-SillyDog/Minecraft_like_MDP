
import random

from src.algorithms.product_mdp import transition


def init_Q(env, rm, q_init=0.0):
    """初始化 Q[(s, u)][a]。"""
    Q = {}
    for s in env.positions:
        for u in rm.states:
            Q[(s, u)] = {a: q_init for a in env.actions}
    return Q


def select_action(Q, s, u, epsilon, actions, rng):
    """ε-greedy；并列最优动作随机选择。"""
    if rng.random() < epsilon:
        return rng.choice(actions)
    qsa = Q[(s, u)]
    qmax = max(qsa.values())
    best = [a for a in actions if qsa[a] == qmax]
    return rng.choice(best)


def q_update(Q, s, u, a, r, s_next, u_next, terminal, alpha, gamma):
    # 终止转移没有后续状态价值。
    if terminal:
        target = r
    else:
        target = r + gamma * max(Q[(s_next, u_next)].values())
    Q[(s, u)][a] += alpha * (target - Q[(s, u)][a])


def evaluate(Q, env, rm, start, n_episodes, max_steps, gamma, rng):
    """运行贪心策略；并列最优动作随机选择，不更新 Q 表。"""
    episode_returns = []
    step_counts = []
    successes = 0
    for _ in range(n_episodes):
        s = start
        u = rm.initial_state
        episode_return = 0.0
        episode_steps = 0
        done = False
        # 评估关闭 ε 探索，但并列最优动作仍随机选择。
        while episode_steps < max_steps and not done:
            qsa = Q[(s, u)]
            qmax = max(qsa.values())
            best = [a for a in env.actions if qsa[a] == qmax]
            a = rng.choice(best)
            s_next, u_next, reward, done = transition(env, rm, s, u, a)
            episode_return += (gamma ** episode_steps) * reward
            s, u = s_next, u_next
            episode_steps += 1
        episode_returns.append(episode_return)
        step_counts.append(episode_steps if done else max_steps)
        if done:
            successes += 1
    return {
        "success_rate": successes / n_episodes,
        "mean_return": sum(episode_returns) / n_episodes,
        "mean_steps": sum(step_counts) / n_episodes,
    }


def train_q_learning(env, rm, start, n_interactions, eval_every=500,
                     eval_episodes=10, max_steps=100, gamma=0.99,
                     alpha=0.1, epsilon=0.1, seed=0, q_init=0.0):
    # 评估使用独立随机数生成器，不改变训练轨迹。
    train_rng = random.Random(seed)
    eval_rng = random.Random(seed)
    Q = init_Q(env, rm, q_init)
    log = []
    interaction = 0
    while interaction < n_interactions:
        s = start
        u = rm.initial_state
        episode_steps = 0
        while (
            interaction < n_interactions
            and episode_steps < max_steps
            and not rm.is_terminal(u)
        ):
            a = select_action(Q, s, u, epsilon, env.actions, train_rng)
            s_next, u_next, reward, terminal = transition(env, rm, s, u, a)
            q_update(
                Q, s, u, a, reward, s_next, u_next, terminal, alpha, gamma
            )
            s, u = s_next, u_next
            interaction += 1
            episode_steps += 1
            if interaction % eval_every == 0:
                stats = evaluate(
                    Q, env, rm, start, eval_episodes, max_steps, gamma, eval_rng
                )
                stats["step"] = interaction
                log.append(stats)
    return Q, log
