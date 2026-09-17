"""环境状态与 RM 状态组成的乘积 MDP。"""


def rm_states(rm):
    return sorted(rm.states)


def product_states(env, rm):
    us = rm_states(rm)
    return [(s, u) for s in env.positions for u in us]


def transition(env, rm, s, u, action):
    """组合环境转移、位置标签和 RM 转移。"""
    # 终止乘积状态保持吸收。
    if rm.is_terminal(u):
        return s, u, 0.0, True
    s_next = env.next_position(s, action)
    # RM 根据动作后位置的标签推进。
    labels = env.label(s_next)
    u_next, reward = rm.next_state(u, labels)
    return s_next, u_next, float(reward), rm.is_terminal(u_next)
