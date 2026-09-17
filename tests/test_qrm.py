"""QRM 反事实更新和训练测试。"""

import unittest

from src.algorithms.q_learning import init_Q, q_update
from src.algorithms.qrm import qrm_update, train_qrm
from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


def load_task(name="coffee_office"):
    env = OfficeWorld(load_officeworld_config())
    rm = RewardMachine(load_reward_machine_config(name))
    return env, rm


class TestQRM(unittest.TestCase):

    def test_one_experience_updates_non_terminal_rm_states(self):
        env, rm = load_task()
        Q = init_Q(env, rm)
        Q[((4, 2), "u1")] = {"U": 0.1, "D": 0.2, "L": 0.3, "R": 0.4}
        Q[((3, 2), "u0")]["D"] = 0.1
        Q[((3, 2), "u1")]["D"] = 0.2

        qrm_update(
            Q, rm, (3, 2), "D", (4, 2), {"coffee"}, 0.1, 0.99
        )

        # 同一条环境经验更新所有非终止 RM 状态，终止状态 u2 不更新。
        self.assertAlmostEqual(Q[((3, 2), "u0")]["D"], 0.1296)
        self.assertAlmostEqual(Q[((3, 2), "u1")]["D"], 0.2196)
        self.assertEqual(Q[((3, 2), "u2")]["D"], 0.0)

    def test_actual_state_update_matches_q_learning(self):
        env, rm = load_task()
        Q_ql = init_Q(env, rm)
        Q_qrm = init_Q(env, rm)
        for Q in [Q_ql, Q_qrm]:
            Q[((4, 2), "u1")] = {
                "U": 0.1, "D": 0.2, "L": 0.3, "R": 0.4,
            }
            Q[((3, 2), "u0")]["D"] = 0.1

        q_update(
            Q_ql, (3, 2), "u0", "D", 0.0, (4, 2), "u1", False, 0.1, 0.99
        )
        qrm_update(
            Q_qrm, rm, (3, 2), "D", (4, 2), {"coffee"}, 0.1, 0.99
        )

        # 对真实 RM 状态的更新应与普通 Q-learning 完全一致。
        self.assertAlmostEqual(
            Q_ql[((3, 2), "u0")]["D"],
            Q_qrm[((3, 2), "u0")]["D"],
        )

    def test_training_computes_one_environment_transition(self):
        env, rm = load_task()
        original = env.next_position
        calls = []

        def counted(position, action):
            calls.append((position, action))
            return original(position, action)

        # 反事实更新可以有多次，但真实环境在一步训练中只转移一次。
        env.next_position = counted
        train_qrm(
            env, rm, env.start, n_interactions=1,
            eval_every=2, eval_episodes=1, max_steps=50, seed=0,
        )
        self.assertEqual(len(calls), 1)

    def test_evaluation_does_not_change_training(self):
        env, rm = load_task()
        # 评估频率不应消耗训练过程使用的随机数。
        Q_50, _ = train_qrm(
            env, rm, env.start, n_interactions=300,
            eval_every=50, eval_episodes=5, max_steps=50, seed=0,
        )
        Q_100, _ = train_qrm(
            env, rm, env.start, n_interactions=300,
            eval_every=100, eval_episodes=5, max_steps=50, seed=0,
        )
        self.assertEqual(Q_50, Q_100)

    def test_learns_visit_abcd(self):
        env, rm = load_task("visit_abcd")
        _, log = train_qrm(
            env, rm, env.start, n_interactions=20000,
            eval_every=1000, eval_episodes=20, max_steps=200, seed=0,
        )
        self.assertGreater(log[-1]["success_rate"], 0.5)
