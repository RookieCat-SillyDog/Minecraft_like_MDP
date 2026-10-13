"""Book 任务的目标经验和表格型 h-DQN 接入。"""

import unittest
from dataclasses import replace

from experiments import run_hrm_craftworld_book as experiment
from src.algorithms.tabular_hdqn import train_tabular_hdqn
from src.config import load_hrm_craftworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


class TestBookTask(unittest.TestCase):
    def setUp(self):
        self.task = experiment.BookTask(
            OfficeWorld(load_hrm_craftworld_config()),
            RewardMachine(load_reward_machine_config("hrm_craftworld_book")),
        )

    def test_arrival_rewards_an_unselected_goal(self):
        state = ((0, 5), "v0")
        next_state, _, reward, reached, _ = self.task.step(state, "rabbit", "R")
        self.assertEqual((reward, reached), (0.0, False))
        self.assertEqual(self.task.low_goal_rewards(state, next_state), [
            ("sugarcane", 1.0, True),
            ("rabbit", 0.0, False),
            ("workbench", 0.0, False),
            ("table", 0.0, False),
        ])
        # 离开脚下的甘蔗时，不为已到达目标再写入导航经验。
        rewards = self.task.low_goal_rewards(next_state, state)
        self.assertNotIn("sugarcane", [goal for goal, _, _ in rewards])

    def test_book_budget_reaches_joint_training(self):
        self.assertEqual(experiment.config.pretrain_interactions, 0)
        self.assertLess(experiment.config.pretrain_interactions, experiment.n_interactions)
        config = replace(experiment.config, anneal_steps=100)
        low, high, log = train_tabular_hdqn(
            self.task, config, 1000, eval_every=500, eval_episodes=1, seed=0,
        )
        self.assertTrue(low)
        self.assertTrue(high)
        self.assertEqual([row["step"] for row in log], [500, 1000])


if __name__ == "__main__":
    unittest.main()
