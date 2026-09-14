"""三因子 Minecraft MDP 的 Day 11-12 测试。"""

import unittest
from dataclasses import replace

from env.factored_minecraft.environment import FactoredMinecraftMDP
from env.factored_minecraft.maps import beef, default_map, key, location
from env.factored_minecraft.tasks import task_rules
from analysis.plot_factored_tasks import LABELS


class TestFactoredMinecraftMDP(unittest.TestCase):

    def setUp(self):
        self.env = FactoredMinecraftMDP(default_map)

    def follow(self, actions):
        """从初始状态开始，依次执行一组动作。"""
        state = self.env.initial_state
        for action in actions:
            state = self.env.transitions(state, action)[0][1]
        return state

    def test_three_factor_graphs(self):
        """检查三张基础图的节点、边和展示标签。"""
        self.assertEqual([len(states) for states in default_map.factor_states], [9, 3, 3])
        self.assertEqual([len(moves) for moves in default_map.factor_moves], [20, 2, 2])
        self.assertEqual(
            [set(labels) for labels in LABELS],
            [set(states) for states in default_map.factor_states],
        )

    def test_task_invariants(self):
        """把构图不变量放在测试中检查，而不是每次构造环境时检查。"""
        action_factor = dict(default_map.action_spec)
        self.assertEqual(set(action_factor), {action for action, _ in default_map.action_spec})
        self.assertEqual(len(action_factor), 6)

        action_sets = [
            {action for _, action in moves}
            for moves in default_map.factor_moves
        ]
        self.assertEqual(action_sets[0] & action_sets[1], set())
        self.assertEqual(action_sets[0] & action_sets[2], set())
        self.assertEqual(action_sets[1] & action_sets[2], set())

        for moves in default_map.factor_moves:
            for (source, _), target in moves.items():
                self.assertNotEqual(source, target)

        for rules in task_rules.values():
            env = FactoredMinecraftMDP(default_map, rules)
            self.assertTrue(env.states)

    def test_bfs_reachable_states(self):
        """检查 independent 的 BFS 结果完整、无重复且顺序稳定。"""
        second_env = FactoredMinecraftMDP(default_map)

        self.assertEqual(len(self.env.states), 81)
        self.assertEqual(len(set(self.env.states)), 81)
        self.assertEqual(self.env.states[0], self.env.initial_state)
        self.assertEqual(self.env.states, second_env.states)
        self.assertIn(self.env.goal_state, self.env.states)

    def test_all_successors_stay_reachable(self):
        """检查合法转移确定、奖励正确，且后继仍在 states 中。"""
        reachable_states = set(self.env.states)

        for state in self.env.states:
            for action in self.env.actions(state):
                outcomes = self.env.transitions(state, action)
                self.assertEqual(len(outcomes), 1)

                probability, next_state = outcomes[0]
                self.assertEqual(probability, 1.0)
                self.assertIn(next_state, reachable_states)
                self.assertEqual(self.env.reward(state, action), -1.0)

    def test_each_action_changes_only_its_own_factor(self):
        """检查 Location、Key、Beef 动作只改变对应因子。"""
        for state in self.env.states:
            for action in self.env.actions(state):
                next_state = self.env.transitions(state, action)[0][1]
                changed_indexes = [
                    index
                    for index in range(3)
                    if state[index] != next_state[index]
                ]
                self.assertEqual(changed_indexes, [self.env.action_factor[action]])

    def test_action_order_and_invalid_actions(self):
        """检查动作顺序固定，无效动作不会变成 self-loop。"""
        expected_actions = [
            "up",
            "right",
            "dye",
            "cook",
        ]
        self.assertEqual(self.env.actions(self.env.initial_state), expected_actions)
        self.assertAlmostEqual(self.env.discount_factor, 0.95)

        self.assertNotIn("left", self.env.actions(self.env.initial_state))
        with self.assertRaises(KeyError):
            self.env.transitions(self.env.initial_state, "left")
        with self.assertRaises(KeyError):
            self.env.transitions(self.env.initial_state, "unknown-action")

    def test_markov_state_does_not_depend_on_history(self):
        """两条历史到达同一状态后，应得到相同动作和转移。"""
        state_dye_first = self.follow(["dye", "cook"])
        state_cook_first = self.follow(["cook", "dye"])

        self.assertEqual(state_dye_first, state_cook_first)
        self.assertEqual(
            self.env.actions(state_dye_first),
            self.env.actions(state_cook_first),
        )
        self.assertEqual(
            self.env.transitions(state_dye_first, "up"),
            self.env.transitions(state_cook_first, "up"),
        )

    def test_terminal_state(self):
        """检查目标状态终止，并且不能继续执行动作。"""
        goal_state = self.env.goal_state
        self.assertTrue(self.env.is_terminal(goal_state))
        self.assertEqual(self.env.actions(goal_state), [])

        with self.assertRaises(KeyError):
            self.env.transitions(goal_state, "up")
        with self.assertRaises(KeyError):
            self.env.reward(goal_state, "up")

    def test_bfs_excludes_disconnected_key_state(self):
        """删除 Key=blue 的入边后，BFS 不应声明该状态可达。"""
        moves = list(default_map.factor_moves)
        moves[key] = {
            transition: target
            for transition, target in moves[key].items()
            if target != "blue"
        }
        disconnected_map = replace(default_map, factor_moves=tuple(moves))
        disconnected_env = FactoredMinecraftMDP(disconnected_map)

        self.assertEqual(len(disconnected_env.states), 54)
        for state in disconnected_env.states:
            self.assertNotEqual(state[key], "blue")

        unreachable_state = (
            disconnected_env.initial_state[location],
            "blue",
            disconnected_env.initial_state[beef],
        )
        self.assertNotIn(unreachable_state, disconnected_env.states)


if __name__ == "__main__":
    unittest.main(verbosity=2)
