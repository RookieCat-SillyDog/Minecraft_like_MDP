"""RewardMachine 测试。
"""

import unittest
from pathlib import Path

import yaml

from src.task_fsm.reward_machine import RewardMachine

ROOT = Path(__file__).resolve().parent.parent
RM_DIR = ROOT / "configs" / "reward_machines"


def load_rm(name):
    with (RM_DIR / f"{name}.yaml").open(encoding="utf-8") as f:
        return RewardMachine(yaml.safe_load(f))


class TestCoffeeOffice(unittest.TestCase):

    def setUp(self):
        self.rm = load_rm("coffee_office")

    def test_initial_and_terminal(self):
        self.assertEqual(self.rm.reset(), "u0")
        self.assertEqual(self.rm.states, {"u0", "u1", "u2"})
        self.assertFalse(self.rm.is_terminal("u0"))
        self.assertTrue(self.rm.is_terminal("u2"))

    # (u, labels, u_next, reward, terminal) —— 笔记 §7.3 逐步
    HAPPY = [
        ("u0", [],          "u0", 0, False),
        ("u0", ["coffee"],  "u1", 0, False),
        ("u1", [],          "u1", 0, False),
        ("u1", ["office"],  "u2", 1, True),
    ]

    def test_happy_path(self):
        for u, labels, exp_u, exp_r, exp_t in self.HAPPY:
            with self.subTest(u=u, labels=labels):
                u_next, r = self.rm.next_state(u, labels)
                self.assertEqual(u_next, exp_u)
                self.assertEqual(r, exp_r)
                self.assertEqual(self.rm.is_terminal(u_next), exp_t)

    def test_premature_office_keeps_u0(self):
        u_next, r = self.rm.next_state("u0", ["office"])
        self.assertEqual((u_next, r), ("u0", 0))

    def test_unrelated_label_keeps_state(self):
        for labels in ([], ["A"], ["D"]):
            with self.subTest(labels=labels):
                u_next, r = self.rm.next_state("u0", labels)
                self.assertEqual((u_next, r), ("u0", 0))

    def test_self_loop_on_plain_cell(self):
        u_next, r = self.rm.next_state("u1", [])
        self.assertEqual((u_next, r), ("u1", 0))

    def test_terminal_absorbing(self):
        for labels in ([], ["coffee"], ["office"], ["A"]):
            with self.subTest(labels=labels):
                u_next, r = self.rm.next_state("u2", labels)
                self.assertEqual((u_next, r), ("u2", 0))
                self.assertTrue(self.rm.is_terminal(u_next))

    def test_reward_lookup(self):
        self.assertEqual(self.rm.reward("u0", "u1"), 0)
        self.assertEqual(self.rm.reward("u1", "u2"), 1)
        self.assertEqual(self.rm.reward("u0", "u0"), 0)  # 自环未定义
        self.assertEqual(self.rm.reward("u2", "u2"), 0)  # 终止吸收


class TestVisitABCD(unittest.TestCase):

    def setUp(self):
        self.rm = load_rm("visit_abcd")

    def test_initial_and_terminal(self):
        self.assertEqual(self.rm.reset(), "v0")
        self.assertEqual(self.rm.states, {"v0", "v1", "v2", "v3", "v4"})
        self.assertFalse(self.rm.is_terminal("v0"))
        self.assertTrue(self.rm.is_terminal("v4"))

    # (u, labels, u_next, reward, terminal) —— 笔记 §8.2 逐步 16 步
    HAPPY = [
        ("v0", [],    "v0", 0, False),
        ("v0", [],    "v0", 0, False),
        ("v0", [],    "v0", 0, False),
        ("v0", ["A"], "v1", 0, False),
        ("v1", [],    "v1", 0, False),
        ("v1", ["B"], "v2", 0, False),
        ("v2", [],    "v2", 0, False),
        ("v2", ["C"], "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", [],    "v3", 0, False),
        ("v3", ["D"], "v4", 1, True),
    ]

    def test_happy_path(self):
        for u, labels, exp_u, exp_r, exp_t in self.HAPPY:
            with self.subTest(u=u, labels=labels):
                u_next, r = self.rm.next_state(u, labels)
                self.assertEqual(u_next, exp_u)
                self.assertEqual(r, exp_r)
                self.assertEqual(self.rm.is_terminal(u_next), exp_t)

    def test_premature_b_at_v0(self):
        u_next, r = self.rm.next_state("v0", ["B"])
        self.assertEqual((u_next, r), ("v0", 0))

    def test_premature_d_at_v1(self):
        u_next, r = self.rm.next_state("v1", ["D"])
        self.assertEqual((u_next, r), ("v1", 0))

    def test_unrelated_label_keeps_state(self):
        for u in ("v0", "v1", "v2", "v3"):
            with self.subTest(u=u):
                u_next, r = self.rm.next_state(u, ["coffee"])
                self.assertEqual((u_next, r), (u, 0))

    def test_terminal_absorbing(self):
        for labels in ([], ["D"], ["A"]):
            with self.subTest(labels=labels):
                u_next, r = self.rm.next_state("v4", labels)
                self.assertEqual((u_next, r), ("v4", 0))

    def test_reward_lookup(self):
        self.assertEqual(self.rm.reward("v3", "v4"), 1)
        self.assertEqual(self.rm.reward("v0", "v1"), 0)
        self.assertEqual(self.rm.reward("v4", "v4"), 0)


if __name__ == "__main__":
    unittest.main()
