"""固定六地标、二值到达奖励的 Delivery 任务接口。"""

from src.envs.officeworld import OfficeWorld


goals = ("p_a", "p_b", "p_c", "d_a", "d_b", "d_c")


class DeliveryTask:
    # 接入新算法的 task 接口；高层状态为 (position, rm_state)。
    actions = OfficeWorld.actions

    def __init__(self, env, rm):
        self.env = env
        self.rm = rm

    def reset(self):
        return self.env.start, self.rm.initial_state

    def legal_goals(self, state):
        # 只排除脚下的地标，不根据RM进度限制取送顺序。
        current_labels = self.env.label(state[0])
        return tuple(goal for goal in goals if goal not in current_labels)

    def low_state(self, state):
        return state[0]

    def low_goal_rewards(self, state, next_state):
        # 同一次移动可为多个目标提供经验；脚下地标已到达，不再生成其经验。
        next_labels = self.env.label(next_state[0])
        rewards = []
        for goal in self.legal_goals(state):
            reached = goal in next_labels
            rewards.append((goal, float(reached), reached))
        return rewards

    def step(self, state, goal, action):
        position, rm_state = state
        next_position = self.env.next_position(position, action)
        labels = self.env.label(next_position)
        next_rm_state, external_reward = self.rm.next_state(rm_state, labels)
        goal_reached = goal in labels
        # 只奖励到达所选地标，不加距离奖励或每步代价。
        intrinsic_reward = 1.0 if goal_reached else 0.0
        return (
            (next_position, next_rm_state), external_reward, intrinsic_reward,
            goal_reached, self.rm.is_terminal(next_rm_state),
        )

    def is_success(self, state):
        return self.rm.is_terminal(state[1])
