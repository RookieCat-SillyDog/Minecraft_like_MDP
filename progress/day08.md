# Day 08

## 今日目标

从 Minecraft-like MDP 的初始状态出发遍历完整转移图，统计理论状态、实际可达状态和状态转移，检查非法、重复及不可达状态，并生成部分状态转移图。

## 完成情况

创建 `experiments/enumerate_minecraft_states.py`，并把绘图细节放在独立的 `experiments/minecraft_state_graph.py` 中。枚举程序实现了：

- 按 `(row, col, wood, iron, bridge)` 五个变量生成理论状态空间。
- 从初始状态开始，通过统一 MDP 接口进行广度优先搜索，不使用 `env.states` 作为待遍历状态列表。
- 记录包含源状态、动作、概率和下一状态的完整转移。
- 比较遍历得到的状态与环境声明的状态，检查遗漏、额外和重复状态。
- 对不可达状态进行互斥分类，并输出数量与示例。
- 统计可达状态—动作对及其带概率转移结果。
- 生成包含动作分支、两种资源收集顺序和 factory 合成条件的部分状态转移图。每个状态节点使用实际 $5\times5$ Grid 展示 Agent 位置，并结合颜色和状态元组显示 `(w,i,b)` 的同步变化。

创建 `tests/test_minecraft_state_enumeration.py`，包含 6 项自动测试。生成的状态图保存在：

- `figures/day08_partial_state_graph.png`
- `figures/day08_partial_state_graph.svg`



## 验证结果

运行枚举程序：

```text
python -B experiments/enumerate_minecraft_states.py
```

得到以下结果：

- 理论状态组合：200 个。
- 从初始状态实际可达：96 个。
- 理论空间中不可达：104 个。
- 状态—动作对：380 个。
- 带概率的转移结果：380 个。
- 环境声明状态、遍历状态和转移记录均无重复。
- 遍历状态与环境声明状态完全一致，且没有落在理论组合之外的状态。

104 个不可达状态可完整分为：

- `bridge=1` 但不是唯一终止状态：99 个。
- 位于 wood 但 wood 标志为 0：2 个。
- 位于 iron 但 iron 标志为 0：2 个。
- 资源齐全并位于 factory 但 bridge 标志为 0：1 个。

单独运行 Day 8 测试：

```text
python -B -m unittest tests.test_minecraft_state_enumeration -v
```

结果为 6 项测试全部通过。

运行完整测试：

```text
python -B -m unittest discover -s tests -v
```

结果为 38 项测试全部通过，Day 8 实现没有破坏已有环境和动态规划算法测试。

## 遇到的问题

首次使用文件路径直接运行枚举脚本时，Python 无法从 `experiments/` 找到项目根目录下的 `env` 包。随后为直接执行入口补充项目根目录路径，同时保留模块方式运行。修正后直接运行和模块运行均成功。

转移数量按照 MDP 的状态—动作对统计。当前有 95 个非终止状态，每个状态有 4 个合法动作，因此共有 380 个状态—动作对；环境是确定性的，所以对应 380 个带概率转移结果。

不确定当前地图示例是不是好的，要不要引入障碍物？以及怎么引入更复杂的地图元素？

## 下一步

Day 09 直接复用第一周的 Policy Iteration 和 Value Iteration，在 96 个可达状态上比较价值，输出最大价值差、最优路径与资源收集顺序，并检查策略循环和并列最优动作。
