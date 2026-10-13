"""环境、事件检测和 Reward Machine 的端到端路线测试。"""

import unittest

from src.config import load_map_config, load_task_config
from src.envs.minecraft_grid import GridWorld
from src.task_fsm.labeling import detect_events
from src.task_fsm.reward_machine import RewardMachine


class TestRoutes(unittest.TestCase):

    def run_route(self, condition, actions):
        env = GridWorld(load_map_config())
        rm = RewardMachine(load_task_config(condition))
        u = rm.reset()
        events_seen = []
        rewards = []
        for action in actions:
            before = env.state
            after = env.step(action)
            events = detect_events(before, after, env.objects)
            u, reward = rm.next_state(u, events)
            events_seen.extend(events)
            rewards.append(reward)
        return rm, u, events_seen, rewards

    def test_condition_a_route(self):
        # 完整路线同时覆盖环境交互、事件生成和 RM 状态推进。
        actions = [
            "U", "U", "R", "R",
            "D", "D", "D", "D",
            "R", "R", "U", "U",
        ]
        rm, u, events, rewards = self.run_route("A", actions)
        self.assertEqual(
            events,
            ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"],
        )
        self.assertTrue(rm.is_terminal(u))
        self.assertEqual(sum(rewards), 1)

    def test_condition_b_routes(self):
        routes = [
            (
                ["U", "U", "R", "R", "R", "R", "D", "D"],
                ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"],
            ),
            (
                ["D", "D", "R", "R", "R", "R", "U", "U"],
                ["GET_BEEF", "COOK", "REACH_GOAL"],
            ),
        ]
        for actions, expected_events in routes:
            with self.subTest(expected_events=expected_events):
                rm, u, events, rewards = self.run_route("B", actions)
                self.assertEqual(events, expected_events)
                self.assertTrue(rm.is_terminal(u))
                self.assertEqual(sum(rewards), 1)

    def test_reaching_goal_early_does_not_finish_condition_a(self):
        # 条件 A 强制执行完整顺序，提前到达目标不算完成。
        actions = [
            "U", "U", "R", "R", "R", "R", "D", "D",
        ]
        rm, u, events, rewards = self.run_route("A", actions)
        self.assertEqual(events, ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"])
        self.assertEqual(u, "u2")
        self.assertFalse(rm.is_terminal(u))
        self.assertEqual(sum(rewards), 0)
