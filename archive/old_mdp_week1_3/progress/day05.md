# Day 05

## 今日目标

实现 Value Iteration（价值迭代），在确定性 5×5 GridWorld 上记录 Bellman residual和停止过程，并与 Policy Iteration的最优价值及策略进行交叉验证。

## 完成情况

完成了 `algorithms/value_iteration.py`：

- 使用 `find_best_actions` 比较一个状态下的全部合法动作，并通过 `tie_tolerance` 保留所有并列最优动作。
- 使用 `greedy_policy` 从最终价值函数中提取确定性贪心策略；存在并列最优动作时选择动作列表中的第一个。
- 使用 `ValueIteration` 从全零价值开始执行同步 Bellman 最优更新。
- 记录每轮贝尔曼残差、迭代次数和是否达到停止阈值。
- 终止状态价值固定为 0。

完成了 `tests/test_value_iteration.py`，包括 8 项测试（ai辅助完成）：

1. `test_all_actions_are_tied_with_zero_values`：检查全零价值下起点的四个动作并列最优。
2. `test_find_best_actions_selects_right`：检查右侧状态价值更高时能够选出唯一最优动作。
3. `test_greedy_policy_is_deterministic`：检查贪心策略为每个非终止状态选择一个概率为 1 的动作。
4. `test_value_iteration_converges`：检查算法达到残差阈值，并保持终止状态价值为 0。
5. `test_start_value_matches_shortest_path`：检查起点价值等于八步最短路径的理论折扣回报。
6. `test_final_policy_is_greedy`：检查最终策略选择的动作属于并列最优动作集合。
7. `test_pi_and_vi_values_are_consistent`：比较 PI 与 VI 在全部状态上的最优价值。
8. `test_invalid_parameters`：检查非法容差和迭代次数能够报告错误。

完成了 `experiments/run_value_iteration.py`：

- 在同一个 GridWorld 和相同数值精度下运行 PI 与 VI。
- 比较两个算法在全部状态上的价值，并输出最大绝对差。
- 检查策略动作不同的状态；如果动作不同，判断两个动作是否均属于并列最优动作。
- 输出 VI 的迭代次数、最终残差、起点价值、最优策略和起点到终点路径。
- 生成以下实验图片：
  - `figures/day05_value_iteration_policy.png`
  - `figures/day05_value_iteration_policy.svg`
  - `figures/day05_value_iteration_convergence.png`
  - `figures/day05_value_iteration_convergence.svg`

## 验证结果

单独运行 Day 05 的测试：

```powershell
python -m unittest tests.test_value_iteration -v
```

8 项 Value Iteration 测试全部通过。

运行全部测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -t . -v
```

实际输出摘要：

```text
Ran 24 tests
OK
```

运行 Day 05 实验：

```powershell
python -m experiments.run_value_iteration
```

实际结果摘要：

```text
是否达到停止条件：True
价值迭代轮数：9
最终残差：0
起点最优价值：-5.69532790
全部状态最大价值差：0
策略动作不同的状态数：0
```

VI 的贝尔曼残差依次为：

```text
1.0, 0.9, 0.81, 0.729, 0.6561, 0.59049, 0.531441, 0.4782969, 0.0
```

最终策略给出的起点到终点路径为：

```text
(0, 0) -> (1, 0) -> (2, 0) -> (3, 0) ->
(4, 0) -> (4, 1) -> (4, 2) -> (4, 3) -> (4, 4)
```

该路径共 8 步。对应的理论折扣回报为：

$$
-\sum_{t=0}^{7}0.9^t=-5.6953279
$$

程序输出与理论值一致。PI 与 VI 在全部 22 个合法状态上的最大价值差为 0，当前确定性动作选择规则下，两种算法输出的策略也完全一致。

## 遇到的问题


1. 贝尔曼残差需要比较全部状态的新旧价值，不能只使用状态循环结束后留下的最后一个 `state`。当前实现使用生成器计算全部状态价值变化的最大值。
2. PI/VI 价值差保存在以状态为键、浮点差值为值的字典中。最初误对单个浮点值调用 `values()`，修改为对整个 `differences` 字典调用 `differences.values()` 后，实验能够正常运行。
3. 没有很理解value iteration的真正价值？算法公式上和policy evaluation很像，只是对于每个状态的价值，从固定策略动作价值变成了所有动作取最高价值(max Q(s,a))，那么代价是什么？整个运行流程比policy iteration简单很多，看起来完全是更简洁的算法，那还要policy iteration干啥？
4. 对贝尔曼残差与最优价值误差之间的关系还没有完全理解。教材里

   $$
   \lVert U_{k+1}-U_k\rVert_\infty \le \delta
   $$

   时，价值迭代结果与最优价值函数之间的误差可以限制在

   $$
   \epsilon=\frac{\delta\gamma}{1-\gamma}
   $$

   以内。为啥相邻两轮的差值能推出当前价值函数与未知的 $U^*$ 之间差，以及公式中的 $\gamma/(1-\gamma)$ 是哪推导的。以及这里的误差值的是更新后的 $U_{k+1}$，还是更新前的 $U_k$；实际设置 `tolerance` 时，是否应根据目标误差 $\epsilon$ 反推 $\delta$。

## 下一步

整理第一周的 MDP 定义、三种动态规划算法、价值图、策略图、收敛结果以及 PI/VI 一致性检查。报告完成并验证后，再开始 Day 06 的 Minecraft-like MDP 书面定义。
