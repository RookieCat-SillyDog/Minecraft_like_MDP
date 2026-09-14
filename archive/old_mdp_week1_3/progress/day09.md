# Day 09

## 今日目标

在 Minecraft-like MDP 上直接复用第一周实现的 Policy Iteration（PI）和 Value Iteration（VI），比较两个算法在全部可达状态上的最优价值，并检查最优策略、执行路径和资源收集顺序。

## 完成情况

创建了 `experiments/run_minecraft.py`，实验代码直接调用已有的 `PolicyIteration` 和 `ValueIteration`，没有为 Minecraft 复制或修改专用算法。实验完成了以下工作：

- 在同一个 `MinecraftMDP` 环境上分别运行 PI 和 VI。
- 比较两个算法在 96 个可达状态上的价值。
- 从初始状态执行两个确定性策略，记录状态、动作、资源收集顺序和折扣回报。
- 检查策略是否进入循环，以及最终是否到达 bridge 完成状态。
- 检查 PI 与 VI 动作不同时，两个动作是否均属于并列最优动作。


创建了 `tests/test_minecraft_pi_vi.py`，包含 5 项自动测试，覆盖算法收敛、全部状态价值一致性、最优路径、折扣回报和并列最优动作。

生成了以下实验结果图：

- `figures/day09_minecraft_pi_value_policy.png`
- `figures/day09_minecraft_pi_value_policy.svg`
- `figures/day09_minecraft_vi_value_policy.png`
- `figures/day09_minecraft_vi_value_policy.svg`
- `figures/day09_minecraft_optimal_paths.png`
- `figures/day09_minecraft_optimal_paths.svg`


## 验证结果

运行 Minecraft PI/VI 实验：

```text
python -B experiments/run_minecraft.py
```

得到以下结果：

- PI 在 16 轮策略迭代后稳定。
- VI 在 17 轮价值迭代后收敛，最终 Bellman residual 为 0。
- 两个算法的起点价值均为 `-11.1974666270`。
- 96 个可达状态上的最大价值差为 0，两个价值函数完全一致。
- 两个策略在 23 个状态上选择了不同动作；逐项检查后，这些动作差异全部可以由并列最优解释。
- PI 和 VI 均从初始状态经过 16 步到达终止状态，没有出现状态循环。
- 两条实际执行路径均按 `iron -> wood` 的顺序收集资源，但从 iron 前往 wood 的具体路线不同。
- 两条路径的折扣回报均为 `-11.1974666270`，与各自的起点价值一致。

单独运行 Day 9 测试：

```text
python -B -m unittest tests.test_minecraft_pi_vi -v
```

结果为新增的 5 项测试全部通过。

运行完整测试：

```text
python -B -m unittest discover -s tests
```

结果为 43 项测试全部通过。

## 遇到的问题

最初把 PI 和 VI 路径画在同一张地图上，两条路线及重复经过的路段互相遮挡，无法清楚辨认执行顺序。随后将路径图改为 PI、VI 两个独立面板，用颜色表示当前资源状态，并在位置旁标注到达步数。重复访问的位置显示多个步数，例如 `t=8/16` 表示第 8 步和第 16 步均到达该位置。


## 下一步

Day 10 完善 README、最终报告和复现说明，从干净环境运行全部测试与实验，并准备展示 Minecraft 状态、最优价值、策略差异和最优路径。
