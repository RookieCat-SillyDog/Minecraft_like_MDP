"""GridWorld 核心状态转移测试。"""

import unittest

from src.config import load_map_config
from src.envs.minecraft_grid import GridWorld


class TestGridWorld(unittest.TestCase):

    def setUp(self):
        self.env = GridWorld(load_map_config())

    def follow(self, actions):
        for action in actions:
            self.env.step(action)
        return self.env.state

    def test_movement_and_blocking(self):
        cases = [
            (["U", "U", "R"], (0, 1)),
            (["D", "D", "R"], (4, 1)),
            (["R"], (2, 0)),              # 墙
            (["L"], (2, 0)),               # 边界
            (["U", "U", "U"], (0, 0)),  # 边界
        ]
        for actions, expected in cases:
            with self.subTest(actions=actions):
                self.env.reset()
                self.assertEqual(self.follow(actions)["position"], expected)

    def test_door_requires_key_and_stays_open(self):
        # 从下方绕到门口，没有钥匙时不能穿过门。
        self.follow(["D", "D", "R", "R", "U", "U", "U"])
        self.assertEqual(self.follow(["U"])["position"], (1, 2))
        self.assertFalse(self.env.state["door_open"])

        self.env.reset()
        # 拿到钥匙后开门；离开再返回时门仍保持开启。
        state = self.follow(["U", "U", "R", "R"])
        self.assertEqual(state["position"], (0, 2))
        self.assertTrue(state["door_open"])
        self.assertTrue(self.follow(["D", "U"])["door_open"])

    def test_cooking_requires_beef(self):
        # 先经过牛肉位置，再进入厨房可以完成烹饪。
        state = self.follow(["D", "D", "R", "R", "R"])
        self.assertTrue(state["has_beef"])
        self.assertTrue(state["cooked"])

        self.env.reset()
        # 绕开牛肉到达厨房时不能烹饪。
        state = self.follow([
            "U", "U", "R", "R", "R", "R",
            "D", "D", "D", "D", "L",
        ])
        self.assertEqual(state["position"], (4, 3))
        self.assertFalse(state["has_beef"])
        self.assertFalse(state["cooked"])

    def test_reset_restores_initial_state(self):
        self.follow(["U", "U", "R", "R"])
        self.assertEqual(self.env.reset(), {
            "position": (2, 0),
            "has_key": False,
            "door_open": False,
            "has_beef": False,
            "cooked": False,
        })

    def test_state_snapshot_is_independent(self):
        before = self.env.state
        self.env.step("U")
        self.assertEqual(before["position"], (2, 0))
        self.assertEqual(self.env.state["position"], (1, 0))
