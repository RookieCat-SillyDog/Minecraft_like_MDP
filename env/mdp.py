"""MDP的统一接口。"""

from abc import ABC, abstractmethod


class MDP(ABC):
    """所有 MDP 环境都需要实现的接口。"""

    @property
    @abstractmethod
    def states(self):
        """返回全部状态。"""

    @property
    @abstractmethod
    def initial_state(self):
        """返回初始状态。"""

    @property
    @abstractmethod
    def discount_factor(self) -> float:
        """返回折扣因子。"""

    @abstractmethod
    def actions(self, state):
        """返回当前状态下的合法动作。"""

    @abstractmethod
    def transitions(self, state, action):
        """返回所有（转移概率，下一状态）。"""

    @abstractmethod
    def reward(self, state, action) -> float:
        """返回期望即时奖励。"""

    @abstractmethod
    def is_terminal(self, state) -> bool:
        """判断是否为终止状态。"""
