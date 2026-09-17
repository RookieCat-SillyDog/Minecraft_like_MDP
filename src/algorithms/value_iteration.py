from src.algorithms.product_mdp import product_states, transition


def value_iteration(env, rm, gamma=0.99, tol=1e-8, max_iter=10000,
                    tie_tolerance=1e-8):

    states = product_states(env, rm)
    actions = env.actions
    values = {st: 0.0 for st in states}

    iterations = 0
    residual = 0.0
    converged = False

    # 本轮所有 Bellman backup都读取上一轮 values。
    for i in range(1, max_iter + 1):
        new_values = {}
        for (s, u) in states:
            if rm.is_terminal(u):
                new_values[(s, u)] = 0.0
                continue
            q_values = []
            for action in actions:
                s_next, u_next, reward, _ = transition(env, rm, s, u, action)
                q = reward + gamma * values[(s_next, u_next)]
                q_values.append(q)

            new_values[(s, u)] = max(q_values)

        residual = max(abs(new_values[st] - values[st]) for st in states)
        values = new_values
        iterations = i
        if residual <= tol:
            converged = True
            break

    # 保存每个动作的价值和全部并列最优动作。
    action_values = {}
    policy = {}
    for (s, u) in states:
        if rm.is_terminal(u):
            action_values[(s, u)] = {}
            policy[(s, u)] = []
            continue
        q = {}
        for a in actions:
            s_next, u_next, r, _ = transition(env, rm, s, u, a)
            q[a] = r + gamma * values[(s_next, u_next)]
        action_values[(s, u)] = q
        best_q = max(q.values())
        policy[(s, u)] = [a for a in actions if best_q - q[a] <= tie_tolerance]

    return values, action_values, policy, iterations, residual, converged
