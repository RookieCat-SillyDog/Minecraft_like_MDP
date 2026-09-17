import random

from src.algorithms.q_learning import evaluate, init_Q, q_update, select_action


def qrm_update(Q, rm, s, a, s_next, labels, alpha, gamma):
    """复用一次环境转移，更新所有非终止 RM 状态的 Q 值。"""
    # 每个假设状态分别计算 RM 转移、奖励和终止标记。
    for u_prime in sorted(rm.states):
        if rm.is_terminal(u_prime):
            continue
        u_next, reward = rm.next_state(u_prime, labels)
        q_update(
            Q, s, u_prime, a, reward, s_next, u_next,
            rm.is_terminal(u_next), alpha, gamma,
        )


def train_qrm(env, rm, start, n_interactions, eval_every=500,
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
            # 环境只转移一次，同一条经验用于更新所有 RM 状态。
            s_next = env.next_position(s, a)
            labels = env.label(s_next)
            u_next_actual, _ = rm.next_state(u, labels)
            qrm_update(Q, rm, s, a, s_next, labels, alpha, gamma)
            s, u = s_next, u_next_actual
            interaction += 1
            episode_steps += 1
            if interaction % eval_every == 0:
                stats = evaluate(
                    Q, env, rm, start, eval_episodes, max_steps, gamma, eval_rng
                )
                stats["step"] = interaction
                log.append(stats)
    return Q, log
