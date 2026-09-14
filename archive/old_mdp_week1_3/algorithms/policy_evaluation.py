"""迭代式 Policy Evaluation（策略评估）。

策略在评估过程中保持不变。算法不断使用 Bellman 期望公式更新状态价值，
直到 Bellman residual（贝尔曼残差）小于给定阈值。
"""

from env.mdp import MDP


def uniform_random_policy(mdp: MDP):
    """创建均匀随机策略。

    每个非终止状态下，所有合法动作被选中的概率相同。
    返回格式为：

        {
            state: {action: probability}
        }
    """
    policy = {}

    for state in mdp.states:
        if mdp.is_terminal(state):
            continue

        actions = mdp.actions(state)
        if not actions:
            raise ValueError(f"非终止状态没有合法动作: {state}")

        probability = 1.0 / len(actions)
        policy[state] = {}

        for action in actions:
            policy[state][action] = probability

    return policy


class PolicyEvaluation:
    """计算一个固定随机策略的状态价值函数。"""

    def __init__(
        self,
        mdp: MDP,
        policy,
        tolerance: float = 1e-8,
        max_iterations: int = 10000,
    ):
        if tolerance <= 0:
            raise ValueError("tolerance 必须大于 0")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须大于 0")

        self.mdp = mdp
        self.policy = policy
        self.tolerance = tolerance
        self.max_iterations = max_iterations

        # evaluate() 运行后，可以读取下面四项结果。
        self.values = {}
        self.residuals = []
        self.iterations = 0
        self.converged = False

        self._check_policy()

    def evaluate(self):
        """执行迭代式策略评估并返回状态价值字典。"""
        values = {state: 0.0 for state in self.mdp.states}
        self.residuals = []
        self.converged = False

        for iteration in range(1, self.max_iterations + 1):
            new_values = {}

            for state in self.mdp.states:
                # 项目约定：终止状态没有后续奖励，价值固定为 0。
                if self.mdp.is_terminal(state):
                    new_values[state] = 0.0
                    continue

                state_value = 0.0

                # 对策略可能选择的每个动作求加权平均。
                for action, action_probability in self.policy[state].items():
                    expected_next_value = 0.0

                    # 对动作可能到达的下一状态求期望。
                    for transition_probability, next_state in self.mdp.transitions(
                        state,
                        action,
                    ):
                        expected_next_value += (
                            transition_probability * values[next_state]
                        )

                    action_value = (
                        self.mdp.reward(state, action)
                        + self.mdp.discount_factor * expected_next_value
                    )
                    state_value += action_probability * action_value

                new_values[state] = state_value

            # V_new = T^pi V，因此两轮价值的最大差就是本轮残差。
            residual = max(
                abs(new_values[state] - values[state])
                for state in self.mdp.states
            )
            self.residuals.append(residual)
            values = new_values

            if residual <= self.tolerance:
                self.converged = True
                self.iterations = iteration
                break
            else:
                self.iterations = self.max_iterations

        self.values = values
        return values

    def _check_policy(self):
        """检查每个非终止状态的动作概率之和是否为 1。"""
        for state in self.mdp.states:
            if self.mdp.is_terminal(state):
                continue

            if state not in self.policy:
                raise ValueError(f"策略缺少状态: {state}")

            legal_actions = set(self.mdp.actions(state))
            policy_actions = set(self.policy[state])

            if not policy_actions.issubset(legal_actions):
                raise ValueError(f"策略包含非法动作，状态为: {state}")

            probabilities = self.policy[state].values()

            if any(probability < 0 for probability in probabilities):
                raise ValueError(f"动作概率不能为负数，状态为: {state}")

            probability_sum = sum(probabilities)
            if abs(probability_sum - 1.0) > 1e-9:
                raise ValueError(
                    f"动作概率之和必须为 1，状态 {state} 的概率和为 {probability_sum}"
                )
