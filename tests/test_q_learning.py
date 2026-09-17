"""Q-learning 更新、动作选择和训练测试。"""

import random
import unittest

from src.algorithms.q_learning import init_Q, q_update, select_action, train_q_learning
from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


def load_task():
    env = OfficeWorld(load_officeworld_config())
    rm = RewardMachine(load_reward_machine_config("coffee_office"))
    return env, rm


class TestQLearning(unittest.TestCase):

    def setUp(self):
        self.env, self.rm = load_task()
        self.Q = init_Q(self.env, self.rm)

    def test_q_update(self):
        # 终止转移不应使用下一状态的 Q 值，即使该值被设得很大。
        self.Q[((4, 4), "u2")] = {a: 9.9 for a in self.env.actions}
        self.Q[((4, 3), "u1")]["R"] = 0.5
        q_update(
            self.Q, (4, 3), "u1", "R", 1.0, (4, 4), "u2", True, 0.1, 0.99
        )
        self.assertAlmostEqual(self.Q[((4, 3), "u1")]["R"], 0.55)

        # 非终止转移的手算结果：0.1 + 0.1 * (0.99 * 0.4 - 0.1)。
        self.Q[((4, 2), "u1")] = {"U": 0.1, "D": 0.2, "L": 0.3, "R": 0.4}
        self.Q[((3, 2), "u0")]["D"] = 0.1
        q_update(
            self.Q, (3, 2), "u0", "D", 0.0, (4, 2), "u1", False, 0.1, 0.99
        )
        self.assertAlmostEqual(self.Q[((3, 2), "u0")]["D"], 0.1296)

    def test_select_action(self):
        rng = random.Random(0)
        self.Q[((2, 2), "u0")] = {"U": 0.1, "D": 0.5, "L": 0.2, "R": 0.3}
        for _ in range(20):
            self.assertEqual(
                select_action(
                    self.Q, (2, 2), "u0", 0.0, self.env.actions, rng
                ),
                "D",
            )

        self.Q[((2, 2), "u0")] = {"U": 0.5, "D": 0.5, "L": 0.0, "R": 0.0}
        # 并列最优动作应随机打破平局，不能固定偏向动作列表首项。
        selected = {
            select_action(self.Q, (2, 2), "u0", 0.0, self.env.actions, rng)
            for _ in range(100)
        }
        self.assertEqual(selected, {"U", "D"})

    def test_learns_coffee_office(self):
        _, log = train_q_learning(
            self.env, self.rm, self.env.start, n_interactions=5000,
            eval_every=500, eval_episodes=20, max_steps=50, seed=0,
        )
        self.assertGreater(log[-1]["success_rate"], 0.8)

    def test_evaluation_does_not_change_training(self):
        # 只改变评估频率；训练使用独立随机数时，两张 Q 表应相同。
        Q_50, _ = train_q_learning(
            self.env, self.rm, self.env.start, n_interactions=300,
            eval_every=50, eval_episodes=5, max_steps=50, seed=0,
        )
        Q_100, _ = train_q_learning(
            self.env, self.rm, self.env.start, n_interactions=300,
            eval_every=100, eval_episodes=5, max_steps=50, seed=0,
        )
        self.assertEqual(Q_50, Q_100)
