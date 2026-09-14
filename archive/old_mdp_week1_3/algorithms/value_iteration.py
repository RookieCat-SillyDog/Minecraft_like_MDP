"""Value Iteration（价值迭代）。
"""

from algorithms.policy_iteration import action_value
from env.mdp import MDP


def find_best_actions(
    mdp: MDP,
    values,
    state,
    tie_tolerance: float = 1e-12,
):
    """返回一个状态下的并列最优动作和最优动作价值。
    返回格式为：
        (best_actions, best_value)
    """
    if tie_tolerance < 0:
        raise ValueError("tie_tolerance 不能为负数")

    actions = mdp.actions(state)
    if not actions:
        raise ValueError(f"状态没有合法动作: {state}")

    action_values = {}

    for action in actions:
        action_values[action]=action_value(mdp,values,state,action)

    best_value = max(action_values.values())

    best_actions = []

    for action in actions:
        difference=best_value - action_values[action]
        if difference<= tie_tolerance:
            best_actions.append(action)

    return best_actions, best_value


def greedy_policy(
    mdp: MDP,
    values,
    tie_tolerance: float = 1e-12,
):
    """根据价值函数创建一个确定性贪心策略。

    如果存在并列最优动作，选择环境动作列表中的第一个。
    """
    policy = {}

    for state in mdp.states:
        if mdp.is_terminal(state):
            continue

        best_actions, _ = find_best_actions(
            mdp=mdp,
            values=values,
            state=state,
            tie_tolerance=tie_tolerance,
        )
        policy[state] = {best_actions[0]: 1.0}

    return policy


class ValueIteration:
    """通过反复执行 Bellman 最优更新寻找最优价值函数。"""

    def __init__(
        self,
        mdp: MDP,
        tolerance: float = 1e-8,
        max_iterations: int = 10_000,
        tie_tolerance: float = 1e-12,
    ):
        if tolerance <= 0:
            raise ValueError("tolerance 必须大于 0")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须大于 0")
        if tie_tolerance < 0:
            raise ValueError("tie_tolerance 不能为负数")

        self.mdp = mdp
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.tie_tolerance = tie_tolerance

        # solve() 运行后，可以读取下面五项结果。
        self.policy = {}
        self.values = {}
        self.residuals = []
        self.iterations = 0
        self.converged = False

    def solve(self):
        """运行价值迭代，返回 ``(最优策略, 最优价值函数)``。"""
        # 从全零价值开始。这里的 values 始终表示上一轮价值。
        values = {state: 0.0 for state in self.mdp.states}

        self.policy = {}
        self.values = {}
        self.residuals = []
        self.iterations = 0
        self.converged = False

        for iteration in range(1, self.max_iterations + 1):
            # 使用新字典保存本轮结果，保证所有状态都使用上一轮 values。
            new_values = {}

            for state in self.mdp.states:
                if self.mdp.is_terminal(state):
                    new_values[state] = 0.0
                    continue

                _, best_value = find_best_actions(
                    mdp=self.mdp,
                    values=values,
                    state=state,
                    tie_tolerance=self.tie_tolerance,
                )
                new_values[state] = best_value

            residual=max(abs(new_values[state]-values[state])
                         for state in self.mdp.states)

            self.residuals.append(residual)
            self.iterations = iteration

            # 本轮全部状态计算完成后，才整体替换上一轮价值。
            values = new_values

            if residual <= self.tolerance:
                self.converged = True
                break

        self.values = values

        if not self.converged:
            raise RuntimeError("价值迭代未在最大迭代次数内达到停止阈值")

        # 价值迭代结束后，只需要提取一次贪心策略。
        self.policy = greedy_policy(
            mdp=self.mdp,
            values=self.values,
            tie_tolerance=self.tie_tolerance,
        )

        return self.policy, self.values
