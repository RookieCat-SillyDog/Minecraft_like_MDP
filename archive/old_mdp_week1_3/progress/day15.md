# Day 15

## 目标

修正 Beef gate 的任务语义，区分 action schema（动作模式）与 grounded transition template（具体有向转移模板）两层结构耦合，并完成第三周可视化、报告和验收材料。

## 完成情况

- Beef 只保留 `cook` 和 `cut` 两个动作模式，两个维度都采用 $0\to1\to2$ 的单向阶段转移。
- `cook` 的 6 条具体模板全部要求位于 kitchen；`cut` 的 6 条具体模板全部要求位于 cutting board。切肉需要案板、烹饪需要厨房，不再只限制两个任意挑选的起始转移。
- 三张因子图的 grounded templates 数量为 Location 20、Key 24、Beef 12。
- 分析器同时报告两层结构计数：$S_{i\to j}$ 是 coupled schemas 数，$K_{i\to j}$ 是 coupled grounded templates 数。
- 分析器仍从全部可达联合状态的实际转移结果并集构造模板集合，并能识别动作可用性变化和转移结果变化。
- Query 级 $N_{i\to j}(\tau)$ 继续按路径实际执行的 coupled template 次数计算。

四个 anchors 的结构计数为：

| anchor | $(S_{K\to L},S_{L\to B})$ | $(K_{K\to L},K_{L\to B})$ |
| --- | --- | --- |
| `independent` | (0, 0) | (0, 0) |
| `key_gates_location` | (2, 0) | (2, 0) |
| `location_gates_beef` | (0, 2) | (0, 12) |
| `combined` | (2, 2) | (2, 12) |

`location_gates_beef` 仍在操作类别层面保持 $S_{L\to B}=2$，但不再把它误写成两条具体模板。由于完成 Beef 目标必须执行两次 `cook` 和两次 `cut`，该方向在所有最短路径上的使用范围为 $\mathcal R_{L\to B}=[4,4]$。

## 分析结果

| anchor | $L^*$ | $\mathcal R_{K\to L}$ | $\mathcal R_{L\to B}$ | $\mathcal R_D$ | reachable | shortest paths | PI/VI max diff |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: |
| `independent` | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 | 0 |
| `key_gates_location` | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 | 0 |
| `location_gates_beef` | 10 | [0, 0] | [4, 4] | [5, 8] | 729 | 90 | 0 |
| `combined` | 10 | [1, 1] | [4, 4] | [5, 8] | 594 | 56 | 0 |

活跃方向的 reachable-context 明细如下：

- $K\to L$：$S=2/4$、$K=2/20$、$M=2/144$。
- $L\to B$：$S=2/2$、$K=12/12$、$M=12/12$。

这里每个比值的分子依次是 coupled schemas、coupled templates 和 coupled instances；分母是相应层级的总数。其余四个非对角方向均为 0。

## 可视化与报告

- `experiments/plot_factored_tasks.py` 从环境和分析器结果生成图中数值，不手工填写实验指标。
- 正式报告引用 `week3_three_factor_graph.*`、`week3_joint_value_slices.*` 和 `week3_anchor_comparison.*` 三组图，均提供 PNG 和 SVG。
- 增加两组探索性 distance-delta 图。在固定联合状态下，它们分别展示加入 $K\to L$ 和 $L\to B$ 规则后，到目标的最短距离变化。
- 完成 `docs/week3_report.md`，内容包括 notation table、三因子表示、四个 anchors、结构与查询级耦合、PI/VI 一致性、tie-aware 最短路径分析、nuisance differences 和 held-out recombination 设计。

## 验证

本轮代码修改后实际运行：

```text
python -B -m experiments.analyze_factored_tasks
python -B -m experiments.plot_factored_tasks
python -B -m unittest tests.test_factored_minecraft tests.test_factored_analysis -v
python -B -m unittest discover -s tests -v
python -B MDP/show_factored_mdp.py
```

结果为：分析命令产生上表数值；绘图命令生成五组 PNG 和 SVG；环境与分析专项测试 18 项全部通过；完整测试 66 项全部通过；图结构检查脚本报告 Beef 有 12 条边，并执行一条 10 步终止路径。报告完成后再次运行完整测试，66 项全部通过。



## 仍需理解的部分与当前决定

当前精确终止状态要求 Location、Key 和 Beef 都达到 $(2,2)$。因此，即使 `independent` 没有钥匙门，也必须执行两个 Key 动作；$K\to L$ 规则不会增加“取得钥匙”本身的动作成本，主要改变门的动作可用性、可达状态数和最短路径集合。
