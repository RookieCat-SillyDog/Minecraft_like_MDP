"""Policy Iteration（策略迭代）。
"""

from algorithms.policy_evaluation import PolicyEvaluation
from env.mdp import MDP


def first_action_policy(mdp: MDP):
    """创建一个简单的确定性初始策略。

    对每个非终止状态，选择合法动作列表中的第一个动作。
    """
    policy = {}

    for state in mdp.states:
        if mdp.is_terminal(state):
            continue

        actions = mdp.actions(state)
        if not actions:
            raise ValueError(f"非终止状态没有合法动作: {state}")

        policy[state] = {actions[0]: 1.0}

    return policy


def action_value(mdp: MDP, values, state, action) -> float:
    """计算在 ``state`` 执行 ``action`` 的一步前瞻价值。
    """
    expected_next_value = 0.0

    for transition_probability, next_state in mdp.transitions(state, action):
        if next_state not in values:
            raise ValueError(f"价值函数缺少下一状态: {next_state}")

        expected_next_value += transition_probability * values[next_state]

    immediate_reward = mdp.reward(state, action)
    discounted_future_value = (
        mdp.discount_factor * expected_next_value
    )

    return immediate_reward + discounted_future_value


def _deterministic_action(policy, state):
    """读取确定性策略在一个状态下选择的动作。"""
    if state not in policy:
        raise ValueError(f"策略缺少状态: {state}")

    action_probabilities = policy[state]

    if len(action_probabilities) != 1:
        raise ValueError(f"策略迭代要求确定性策略，状态为: {state}")

    action, probability = next(iter(action_probabilities.items()))

    if abs(probability - 1.0) > 1e-12:
        raise ValueError(f"确定性策略的动作概率必须为 1，状态为: {state}")

    return action


def improve_policy(
    mdp: MDP,
    policy,
    values,
    tie_tolerance: float = 1e-12,
):
    """执行一次策略改进。

    返回 ``(改进后的策略, 是否稳定, 发生变化的状态记录)``。

    """
    if tie_tolerance < 0:
        raise ValueError("tie_tolerance 不能为负数")

    new_policy = {}
    changes = []

    for state in mdp.states:
        if mdp.is_terminal(state):
            continue

        actions = mdp.actions(state)
        if not actions:
            raise ValueError(f"非终止状态没有合法动作: {state}")

        old_action = _deterministic_action(policy, state)
        if old_action not in actions:
            raise ValueError(f"策略包含非法动作，状态为: {state}")

        # 逐个计算合法动作的 Q(s, a)。使用普通循环，便于观察计算过程。
        action_values = {}
        for action in actions:
            action_values[action] = action_value(
                mdp,
                values,
                state,
                action,
            )

        best_value = max(action_values.values())

        # 一个状态可能有多个并列最优动作。
        best_actions = []
        for action in actions:
            difference = best_value - action_values[action]
            if difference <= tie_tolerance:
                best_actions.append(action)

        # 优先保留仍然最优的旧动作；否则使用环境给出的第一个最优动作。
        if old_action in best_actions:
            new_action = old_action
        else:
            new_action = best_actions[0]

        new_policy[state] = {new_action: 1.0}

        if new_action != old_action:
            changes.append((state, old_action, new_action))

    stable = len(changes) == 0
    return new_policy, stable, changes


class PolicyIteration:
    """通过交替执行策略评估和策略改进寻找最优策略。"""

    def __init__(
        self,
        mdp: MDP,
        initial_policy=None,
        evaluation_tolerance: float = 1e-8,
        evaluation_max_iterations: int = 10_000,
        max_iterations: int = 1_000,
        tie_tolerance: float = 1e-12,
    ):
        if evaluation_tolerance <= 0:
            raise ValueError("evaluation_tolerance 必须大于 0")
        if evaluation_max_iterations <= 0:
            raise ValueError("evaluation_max_iterations 必须大于 0")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须大于 0")
        if tie_tolerance < 0:
            raise ValueError("tie_tolerance 不能为负数")

        self.mdp = mdp
        if initial_policy is None:
            self.initial_policy = first_action_policy(mdp)
        else:
            self.initial_policy = initial_policy
        self.evaluation_tolerance = evaluation_tolerance
        self.evaluation_max_iterations = evaluation_max_iterations
        self.max_iterations = max_iterations
        self.tie_tolerance = tie_tolerance

        # solve() 运行后可读取这些结果。
        self.policy = {}
        self.values = {}
        self.history = []
        self.iterations = 0
        self.converged = False

    def solve(self):
        """运行策略迭代，返回 ``(最优策略, 最优价值函数)``。"""
        # 复制初始策略，避免算法修改调用者传入的字典。
        policy = {
            state: action_probabilities.copy()
            for state, action_probabilities in self.initial_policy.items()
        }

        self.history = []
        self.iterations = 0
        self.converged = False
        self.policy = {}
        self.values = {}

        for iteration in range(1, self.max_iterations + 1):
            # 第一步：评估当前策略，得到 V^pi。
            evaluator = PolicyEvaluation(
                mdp=self.mdp,
                policy=policy,
                tolerance=self.evaluation_tolerance,
                max_iterations=self.evaluation_max_iterations,
            )
            values = evaluator.evaluate()

            if not evaluator.converged:
                raise RuntimeError(
                    "策略评估未在最大迭代次数内收敛，不能可靠地执行策略改进"
                )

            # 第二步：根据 V^pi 比较所有动作，得到更好的策略。
            new_policy, stable, changes = improve_policy(
                mdp=self.mdp,
                policy=policy,
                values=values,
                tie_tolerance=self.tie_tolerance,
            )

            self.history.append({
                "iteration": iteration,
                "evaluation_iterations": evaluator.iterations,
                "evaluation_residual": evaluator.residuals[-1],
                "changed_states": len(changes),
                "changes": changes,
                "stable": stable,
            })

            self.iterations = iteration

            # 第三步：没有状态改变时，当前策略已经稳定。
            if stable:
                self.policy = new_policy
                self.values = values
                self.converged = True
                return self.policy, self.values

            # 策略发生变化，下一轮评估新的策略。
            policy = new_policy

        # 达到上限却仍未稳定，说明不能声称算法已经收敛。
        raise RuntimeError("策略迭代未在最大迭代次数内达到稳定")
