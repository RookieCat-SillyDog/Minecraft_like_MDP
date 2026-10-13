"""表格型 h-DQN 的折扣、阶段边界、探索和只读评估。"""

import random
import unittest
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch

from src.algorithms import tabular_hdqn

from src.algorithms.tabular_hdqn import (
    TabularHDQNConfig,
    evaluate_tabular_hdqn,
    low_epsilon,
    replay_updates,
    train_tabular_hdqn,
)


class ToyTask:
    actions = ("move",)

    def __init__(self, goal_at=3, terminal_at=6):
        self.goal_at = goal_at
        self.terminal_at = terminal_at
        self.training_steps = 0

    def reset(self):
        return 0

    def legal_goals(self, state):
        if state == self.terminal_at:
            raise AssertionError("不能在环境终止后查询目标")
        return ("goal",)

    def low_state(self, state):
        return state

    def low_goal_rewards(self, state, next_state):
        reached = next_state % self.goal_at == 0
        return [("goal", float(reached), reached)]

    def step(self, state, goal, action):
        self.training_steps += 1
        next_state = state + 1
        reached = next_state % self.goal_at == 0
        terminal = next_state == self.terminal_at
        return next_state, 1.0, float(reached), reached, terminal

    def is_success(self, state):
        return state == self.terminal_at


class TestTabularHDQN(unittest.TestCase):
    def test_replay_uses_duration_discount_and_goal_termination(self):
        config = TabularHDQNConfig(gamma=0.5, alpha_low=1.0, alpha_high=1.0)
        low = {(0, "goal"): {"move": 0.0}, (3, "goal"): {"move": 10.0}}
        high = {0: {"goal": 0.0}, 3: {"goal": 4.0, "unavailable": 99.0}}
        replay_updates(
            low, high,
            [((0, "goal"), "move", 1.0, (3, "goal"), True)],
            [(0, "goal", 3.0, 3, 3, ("goal",), False)],
            config, random.Random(0),
        )
        self.assertEqual(low[(0, "goal")]["move"], 1.0)
        self.assertEqual(high[0]["goal"], 3.5)
        # 终止经验无需下一状态的 Q 行。
        replay_updates(low, high, [], [(0, "goal", 2.0, 3, 6, (), True)],
                       config, random.Random(0))
        self.assertEqual(high[0]["goal"], 2.0)

    def test_training_discounts_option_rewards_and_stores_duration(self):
        config = TabularHDQNConfig(pretrain_interactions=0, gamma=0.5)
        with patch.object(tabular_hdqn, "_store_experience",
                          wraps=tabular_hdqn._store_experience) as store:
            train_tabular_hdqn(ToyTask(), config, 6, eval_every=10)
        entries = [call.args[1] for call in store.call_args_list
                   if call.args[3] == config.high_memory_size]
        self.assertEqual(entries, [
            (0, "goal", 1.75, 3, 3, ("goal",), False),
            (3, "goal", 1.75, 3, 6, (), True),
        ])

    def test_budget_mid_option_does_not_create_high_experience(self):
        task = ToyTask()
        config = TabularHDQNConfig(pretrain_interactions=0)
        _, high, log = train_tabular_hdqn(task, config, 2, eval_every=10)
        self.assertEqual(task.training_steps, 2)
        self.assertEqual(high, {0: {"goal": 0.0}})
        self.assertEqual(log, [])

    def test_pretraining_boundary_keeps_low_learning_and_restarts_sampling(self):
        task = ToyTask(goal_at=1, terminal_at=1)
        config = TabularHDQNConfig(
            pretrain_interactions=2, alpha_low=1.0, alpha_high=1.0)
        low, high, _ = train_tabular_hdqn(task, config, 2, eval_every=10)
        self.assertEqual(low[(0, "goal")]["move"], 1.0)
        self.assertEqual(high, {})
        _, high, _ = train_tabular_hdqn(ToyTask(goal_at=1, terminal_at=1),
                                       config, 3, eval_every=10)
        self.assertEqual(high[0]["goal"], 1.0)

        # 在未达成目标时切阶段，不把预训练的半段计入高层回报。
        config = replace(config, batch_size=1)
        task = ToyTask()
        _, high, _ = train_tabular_hdqn(task, config, 5, eval_every=10)
        self.assertEqual(task.training_steps, 5)
        self.assertAlmostEqual(high[0]["goal"], 1.0 + config.gamma + config.gamma ** 2)

    def test_option_can_run_beyond_eighty_steps_and_episode_cap_is_terminal(self):
        config = TabularHDQNConfig(
            pretrain_interactions=0, max_episode_steps=120, alpha_high=1.0,
            batch_size=1)
        task = ToyTask(goal_at=100, terminal_at=100)
        _, high, _ = train_tabular_hdqn(task, config, 100, eval_every=200)
        self.assertEqual(task.training_steps, 100)
        self.assertAlmostEqual(high[0]["goal"], sum(config.gamma ** i for i in range(100)))

        config = replace(config, max_episode_steps=2)
        _, high, _ = train_tabular_hdqn(ToyTask(), config, 2, eval_every=10)
        self.assertAlmostEqual(high[0]["goal"], 1.0 + config.gamma)

    def test_exploration_depends_on_goal_success_and_training_steps(self):
        config = TabularHDQNConfig(success_window=10, anneal_steps=100)
        self.assertEqual(low_epsilon([], 0, config), 1.0)
        self.assertAlmostEqual(low_epsilon([False] * 10, 50, config), 0.55)
        self.assertEqual(low_epsilon([True] * 10, 0, config), 0.1)
        self.assertEqual(low_epsilon([False] * 10, 100, config), 0.1)

    def test_pretraining_and_joint_training_use_different_episode_limits(self):
        task = ToyTask(goal_at=100, terminal_at=100)
        config = TabularHDQNConfig(
            pretrain_interactions=5, pretrain_max_episode_steps=3, max_episode_steps=2)
        with patch.object(task, "step", wraps=task.step) as step:
            train_tabular_hdqn(task, config, 9, eval_every=100)
        starts = [call.args[0] for call in step.call_args_list]
        self.assertEqual(starts, [0, 1, 2, 0, 1, 0, 1, 0, 1])
        stats = evaluate_tabular_hdqn(task, {}, {}, config, 1, random.Random(0))
        self.assertEqual(stats["mean_primitive_steps"], 2)

    def test_low_bootstraps_at_rm_termination_and_timeout_but_high_does_not(self):
        config = TabularHDQNConfig(
            pretrain_interactions=0, max_episode_steps=2,
            gamma=0.5, alpha_low=1.0, alpha_high=1.0)
        original_replay = replay_updates

        def seed_next_value(low, high, low_memory, high_memory, config, rng):
            if len(low_memory) == 2:
                low[(2, "goal")]["move"] = 4.0
                high[2] = {"goal": 99.0}
            original_replay(low, high, low_memory, high_memory, config, rng)

        for terminal_at in (2, 10):
            with self.subTest(terminal_at=terminal_at):
                with patch.object(tabular_hdqn, "replay_updates", seed_next_value):
                    low, high, _ = train_tabular_hdqn(
                        ToyTask(terminal_at=terminal_at), config, 2, eval_every=10)
                self.assertEqual(low[(1, "goal")]["move"], 2.0)
                self.assertEqual(high[0]["goal"], 1.5)

    def test_pretraining_low_epsilon_anneals_and_does_not_restart_in_joint_phase(self):
        config = TabularHDQNConfig(pretrain_interactions=4, anneal_steps=4)
        task = ToyTask(goal_at=100, terminal_at=100)
        with patch.object(tabular_hdqn, "select_action",
                          wraps=tabular_hdqn.select_action) as select:
            train_tabular_hdqn(task, config, 7, eval_every=100)
        epsilons = [call.args[2] for call in select.call_args_list
                    if call.args[3] == task.actions]
        for actual, expected in zip(epsilons, [1.0, 0.775, 0.55, 0.325, 0.1, 0.1, 0.1]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(len(epsilons), 7)

    def test_relabeling_learns_a_goal_not_selected_for_behavior(self):
        class TwoGoalTask(ToyTask):
            def legal_goals(self, state):
                return ("goal_a", "goal_b")

            def low_goal_rewards(self, state, next_state):
                return [("goal_a", 0.0, False), ("goal_b", 1.0, True)]

            def step(self, state, goal, action):
                self.selected_goal = goal
                reached = goal == "goal_b"
                return state + 1, 0.0, float(reached), reached, False

        task = TwoGoalTask()
        config = TabularHDQNConfig(pretrain_interactions=1, alpha_low=1.0)
        low, high, _ = train_tabular_hdqn(task, config, 1, eval_every=10, seed=1)
        self.assertEqual(task.selected_goal, "goal_a")
        self.assertEqual(low[(0, "goal_b")]["move"], 1.0)
        self.assertEqual(low[(0, "goal_a")]["move"], 0.0)
        self.assertEqual(high, {})

    def test_evaluation_is_read_only_and_does_not_change_learning(self):
        config = TabularHDQNConfig(pretrain_interactions=0)
        low, high = {(0, "goal"): {"move": 3.0}}, {0: {"goal": 4.0}}
        original_low, original_high = deepcopy(low), deepcopy(high)
        stats = evaluate_tabular_hdqn(
            ToyTask(), low, high, config, 2, random.Random(0))
        self.assertEqual(low, original_low)
        self.assertEqual(high, original_high)
        self.assertEqual(stats["success_rate"], 1.0)
        self.assertEqual(stats["mean_primitive_steps"], 6)
        self.assertEqual(stats["mean_option_count"], 2)

        expected_low, expected_high, _ = train_tabular_hdqn(
            ToyTask(), config, 12, eval_every=100, seed=7)
        low, high, log = train_tabular_hdqn(
            ToyTask(), config, 12, eval_every=1, seed=7)
        self.assertEqual(low, expected_low)
        self.assertEqual(high, expected_high)
        self.assertEqual([row["step"] for row in log], list(range(1, 13)))


if __name__ == "__main__":
    unittest.main()
