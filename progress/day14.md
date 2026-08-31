# Day 14

> 后续修订：本页保留 Day 14 当时的实验记录。Day 15 修改了 Beef 转移与耦合口径，因此本页的 Beef 模板数、$L\to B$ 指标、路径数量和切换范围不代表当前实现；更新后的结果见 `progress/day15.md`。

## 今日目标

在全部最短路径上计算 query-level coupling（查询级耦合）和动作域切换范围，匹配四个 anchors 的 $L^*$，并使用现有 PI 和 VI 完成交叉验证。

## 完成情况

- 创建 `experiments/analyze_factored_tasks.py`。
- 使用 BFS 建立 shortest-path DAG（最短路径有向无环图）。
- 在 DAG 上按联合状态和上一动作因子动态计算最短路径数量、耦合最小值和最大值以及动作域切换范围，没有保存全部路径。
- 从环境的 `actions` 和 `transitions` 枚举实际转移结果，在 reachable-context scope 下计算六个方向的结构耦合明细。
- 报告可达状态数、最短路径数量、合法动作总数、各因子平均合法动作数和平均 branching factor（分支因子）。
- 直接复用现有 PI 和 VI，比较每个环境全部可达状态的价值，并用 action value（动作价值）检查策略差异。
- 新增 8 项分析测试，覆盖门谓词、精确功能区模板、单因子变化、结构矩阵、$K/M$ 与两种比例、非默认 query 起点、路径范围、长度匹配、动作统计和 PI/VI 一致性。

## 分析结果

| anchor | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $N_{K\to L}$ | $N_{L\to B}$ | $D$ | reachable | shortest paths | PI/VI max diff |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |
| `independent` | 0 | 0 | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 | 0 |
| `key_gates_location` | 2 | 0 | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 | 0 |
| `location_gates_beef` | 0 | 2 | 10 | [0, 0] | [1, 1] | [3, 9] | 729 | 10800 | 0 |
| `combined` | 2 | 2 | 10 | [1, 1] | [1, 1] | [3, 9] | 594 | 4068 | 0 |

四个环境的 PI/VI 策略均存在动作差异，但所有差异都能由并列最优动作解释。

激活方向的结构耦合明细为：$K_{K\to L}=2$、$M_{K\to L}=2$、总实例数 144，模板比例和实例比例分别为 $2/20$、$2/144$；$K_{L\to B}=2$、$M_{L\to B}=2$、总实例数 146，两种比例分别为 $2/18$、$2/146$。其余四个非对角方向的 $K$、$M$ 和两种比例均为 0。

## Nuisance differences

钥匙门使 `key_gates_location` 和 `combined` 的可达状态数从 729 降为 594。Key 图没有恢复到 `blank` 的动作；穿门要求先达到 $(2,2)$，因此门两侧支持的 Location–Key 组合不同。两条精确 Beef gates 不进一步减少可达状态集合，所以 `location_gates_beef` 仍为 729，`combined` 与钥匙门任务同为 594；但它们会减少合法动作和最短路径数量，并把最小动作域切换次数从 2 提高到 3。四个任务虽然匹配了 $L^*$，但可达状态数、最短路径数量和平均分支因子没有全部匹配。



## 验证命令

```text
python -B -m experiments.analyze_factored_tasks
python -B -m unittest tests.test_factored_analysis -v
python -B -m unittest discover -s tests -v
```

分析测试共 8 项，factored 环境与分析专项测试合计 16 项。最终完整测试共 64 项，结果全部通过；分析命令确认四个 anchors 的 $L^*$ 均为 10，PI/VI 最大价值差均为 0。

## 遇到的问题

未优化时，四个环境连续运行 PI 超过两分钟仍未完成。原因是动作验证反复扫描固定动作和因子边。加入不改变环境行为的查找表与合法动作缓存后，完整分析能够稳定完成。复审还发现最短路径范围最初从 `env.initial_state` 初始化，而 DAG 可以使用 `query_set` 中的起点；现已改为使用 DAG 实际起点，并增加非默认 query 起点测试。
