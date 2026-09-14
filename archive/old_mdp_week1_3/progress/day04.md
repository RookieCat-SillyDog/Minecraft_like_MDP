# Day 04

## 今日目标

实现 Policy Iteration（策略迭代），在确定性 5×5 GridWorld 上交替执行策略评估和策略改进，记录每轮收敛情况，并在策略稳定后停止。

## 完成情况

完成了 `algorithms/policy_iteration.py`：

- 直接复用 Day 03 的迭代式 `PolicyEvaluation`，没有重复实现策略评估。
- 使用 `first_action_policy` 为每个非终止状态创建确定性初始策略。
- 使用 `action_value` 按照一步前瞻公式计算动作价值。
- 使用独立的 `improve_policy` 函数比较所有合法动作并执行策略改进。
- 如果旧动作仍属于并列最优动作，则保留旧动作，避免策略在等价动作之间反复切换。
- 使用 `PolicyIteration` 交替执行策略评估和策略改进，并在全部状态的动作都不再变化时停止。
- 记录每轮策略评估次数、最终 Bellman residual、策略变化状态数和具体动作变化。


完成了 `tests/test_policy_iteration.py`，包括 6 项测试：

1. `test_first_action_policy`：检查初始策略为每个非终止状态选择第一个合法动作，且动作概率为 1。
2. `test_action_value`：检查一步价值包含即时奖励和折扣后的下一状态价值。
3. `test_policy_improvement_changes_bad_action`：检查策略改进能够将价值较低的动作替换为更优动作。
4. `test_policy_improvement_keeps_tied_action`：检查旧动作并列最优时保持原动作不变。
5. `test_policy_iteration_converges`：检查完整策略迭代稳定收敛，最终策略在每个状态都选择动作价值最大的动作。
6. `test_start_value_matches_shortest_path`：检查起点价值等于八步最短路径的理论折扣回报。



完成了 `experiments/run_policy_iteration.py`，用于运行实验、打印每轮收敛记录、输出最优策略和起点到终点路径，并生成：

- `figures/day04_optimal_policy.png`
- `figures/day04_optimal_policy.svg`
- `figures/day04_policy_iteration_convergence.png`
- `figures/day04_policy_iteration_convergence.svg`



## 验证结果

运行全部测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -t . -v
```

实际输出摘要：

```text
Ran 16 tests in 0.138s
OK
```

其中包括 6 项 GridWorld 测试、4 项策略评估测试和 6 项策略迭代测试，全部通过。Day 04 的 6 项测试也已使用以下命令单独运行并通过：

```powershell
python -m unittest tests.test_policy_iteration -v
```

运行 Day 04 实验：

```powershell
python -m experiments.run_policy_iteration
```

实际结果摘要：

```text
是否稳定收敛：True
策略迭代轮数：9
起点最优价值：-5.69532790
```

每轮策略变化状态数依次为：

```text
2, 3, 4, 3, 3, 2, 3, 1, 0
```

第 9 轮没有状态改变，因此满足“策略稳定后停止”的验收要求。最终策略给出的起点到终点路径为：

```text
(0, 0) -> (1, 0) -> (2, 0) -> (3, 0) ->
(4, 0) -> (4, 1) -> (4, 2) -> (4, 3) -> (4, 4)
```

该路径共 8 步，等于无障碍情况下起点到终点的图距离，因此是最短路径。对应理论折扣回报为：

$$
-\sum_{t=0}^{7}0.9^t=-5.6953279
$$

与程序输出一致。最终策略在每个非终止状态选择的动作价值均等于该状态所有合法动作价值的最大值

## 遇到的问题

1. 多个动作可能具有相同的最优动作价值。如果每次策略改进都重新选择并列动作，策略可能在等价动作之间变化，影响稳定性判断。当前实现会在旧动作仍然最优时保留旧动作。
2. 初始策略在多个状态选择撞击边界的动作，因此前八轮的策略评估均需要 176 次迭代才能达到 `1e-8` 阈值。第九轮最优策略没有循环，策略评估只需 9 次迭代，残差即为 0。
3. 测试文件的unnitest还是不熟练，整个测试框架要ai辅助完成。
4. matplotlib库的使用依然需要学习，尤其是颜色、图注和坐标轴标注。

## 下一步

Day 05 实现 Value Iteration（价值迭代），在相同 GridWorld 和数值容差下比较 Policy Iteration 与 Value Iteration 的最优价值，并检查不同策略是否来自并列最优动作。
