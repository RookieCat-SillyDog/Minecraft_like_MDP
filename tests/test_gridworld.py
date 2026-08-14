"""GridWorld 环境测试。"""

import unittest

from env.gridworld import GridWorld


class TestGridWorld(unittest.TestCase):

    def setUp(self):
        self.env = GridWorld()

    def test_configuration_and_actions(self):
        """检查起点、终点、状态和动作。"""
        self.assertEqual(self.env.initial_state, (0, 0))
        self.assertEqual(self.env.goal, (4, 4))
        self.assertEqual(len(self.env.states), 22)
        self.assertEqual(
            self.env.actions((0, 0)),
            list(self.env.ACTIONS),
        )

        for obstacle in self.env.obstacles:
            self.assertNotIn(obstacle, self.env.states)

    def test_normal_movement(self):
        """检查正常移动。"""
        self.assertEqual(
            self.env.transitions((0, 0), self.env.RIGHT),
            [(1.0, (0, 1))],
        )
        self.assertEqual(
            self.env.transitions((0, 0), self.env.DOWN),
            [(1.0, (1, 0))],
        )

    def test_collision_keeps_position(self):
        """检查边界和障碍物碰撞。"""
        self.assertEqual(
            self.env.transitions((0, 0), self.env.UP),
            [(1.0, (0, 0))],
        )
        self.assertEqual(
            self.env.transitions((1, 0), self.env.RIGHT),
            [(1.0, (1, 0))],
        )

    def test_terminal_state(self):
        """检查终止状态。"""
        self.assertTrue(self.env.is_terminal(self.env.goal))
        self.assertEqual(self.env.actions(self.env.goal), [])

        with self.assertRaises(ValueError):
            self.env.transitions(self.env.goal, self.env.UP)

    def test_all_transitions(self):
        """检查全部合法转移。"""
        for state in self.env.states:
            for action in self.env.actions(state):
                transitions = self.env.transitions(state, action)

                self.assertEqual(len(transitions), 1)

                probability, next_state = transitions[0]
                self.assertEqual(probability, 1.0)
                self.assertIn(next_state, self.env.states)

    def test_reward_and_invalid_input(self):
        """检查奖励、折扣因子和非法输入。"""
        self.assertEqual(
            self.env.reward((0, 0), self.env.RIGHT),
            -1.0,
        )
        self.assertAlmostEqual(
            self.env.discount_factor,
            0.9,
        )

        with self.assertRaises(ValueError):
            self.env.actions((99, 99))

        with self.assertRaises(ValueError):
            self.env.transitions((0, 0), 999)


if __name__ == "__main__":
    unittest.main(verbosity=2)