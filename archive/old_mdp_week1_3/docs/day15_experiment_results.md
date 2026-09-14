# Day 15 三因子任务实验结果



## 1. 当前地图

下图是 Location（位置）因子的字符展示。程序中坐标写作 `(row, col)`，原点 `(0,0)` 在左上角。

```text
             col=0           col=1           col=2

row=0       (0,0) --------- (0,1)    W      (0,2)
               |               |               |
row=1     B  (1,0) -------- C (1,1) --D--     (1,2)
               |               |               |
row=2     S  (2,0) --------- (2,1)    W    G  (2,2)
```

- `S` 是起点，`G` 是终点，`B` 是 cutting board（案板），`C` 是 kitchen（厨房）。
- `W` 表示墙，分别阻断 `(0,1) <-> (0,2)` 和 `(2,1) <-> (2,2)`。
- `D` 是 `(1,1) <-> (1,2)` 之间的双向候选门边。在 `key_gates_location` 和 `combined` 中，只有 Key 状态为 `(2,2)` 时才能通过；其他两个 anchor 中它是普通通路。
- 在 `location_gates_beef` 和 `combined` 中，`cook` 只能在 `C` 执行，`cut` 只能在 `B` 执行。

地图只展示联合状态的 Location 坐标；Key 和 Beef 从一开始就是状态因子，不是地图上的拾取物。完整初始状态和目标状态分别为

$$
x_0=((2,0),(0,0),(0,0)),
\qquad
x_G=((2,2),(2,2),(2,2)).
$$

## 2. 环境与计数口径

联合状态为

$$
x=(l,k,b),
$$

其中 Location、Key 和 Beef 三个因子各有 9 个理论状态，理论联合状态数为

$$
9\times9\times9=729.
$$

当前三张 component graph（成分图）的规模为：

| 因子 | 状态数 | Action schemas | Grounded templates |
| --- | ---: | ---: | ---: |
| Location | 9 | 4 | 20 |
| Key | 9 | 4 | 24 |
| Beef | 9 | 2 | 12 |

Beef 使用两个动作模式：`cook` 令 cooking 维度按 $0\to1\to2$ 前进，`cut` 令 processing 维度按 $0\to1\to2$ 前进。6 条 `cook` templates 全部要求 kitchen，6 条 `cut` templates 全部要求 cutting board。

本文区分以下指标：

- $S_{i\to j}$：受因子 $i$ 控制的 factor-$j$ action schema（动作模式）数；
- $K_{i\to j}$：受因子 $i$ 控制的 factor-$j$ grounded template（具体有向模板）数；
- $M_{i\to j}$：coupled templates 在 factor-$i$ context 中的合法实例数；
- $N_{i\to j}(\tau)$：路径 $\tau$ 实际执行 coupled templates 的次数；
- $D(\tau)$：相邻动作在 Location、Key、Beef 三个动作域之间的切换次数。

## 3. 四个 Anchor 的主结果

| anchor | $S_{K\to L}$ | $S_{L\to B}$ | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $N_{K\to L}$ | $N_{L\to B}$ | $D$ | reachable | shortest paths | PI/VI max diff |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |
| `independent` | 0 | 0 | 0 | 0 | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 | 0 |
| `key_gates_location` | 2 | 0 | 2 | 0 | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 | 0 |
| `location_gates_beef` | 0 | 2 | 0 | 12 | 10 | [0, 0] | [4, 4] | [5, 8] | 729 | 90 | 0 |
| `combined` | 2 | 2 | 2 | 12 | 10 | [1, 1] | [4, 4] | [5, 8] | 594 | 56 | 0 |

四个 anchors 的最优原语长度都为 $L^*=10$，因此路径长度已经匹配。但可达状态数、最短路径数量、动作可用性和动作域切换范围并未全部匹配。

## 4. 两层结构耦合矩阵

矩阵的行是 conditioning factor（条件因子），列是 transition 被改变的因子，顺序均为 Location、Key、Beef。

| anchor | Schema matrix $\mathbf S$ | Template matrix $\mathbf K$ |
| --- | --- | --- |
| `independent` | $\begin{bmatrix}0&0&0\\0&0&0\\0&0&0\end{bmatrix}$ | $\begin{bmatrix}0&0&0\\0&0&0\\0&0&0\end{bmatrix}$ |
| `key_gates_location` | $\begin{bmatrix}0&0&0\\2&0&0\\0&0&0\end{bmatrix}$ | $\begin{bmatrix}0&0&0\\2&0&0\\0&0&0\end{bmatrix}$ |
| `location_gates_beef` | $\begin{bmatrix}0&0&2\\0&0&0\\0&0&0\end{bmatrix}$ | $\begin{bmatrix}0&0&12\\0&0&0\\0&0&0\end{bmatrix}$ |
| `combined` | $\begin{bmatrix}0&0&2\\2&0&0\\0&0&0\end{bmatrix}$ | $\begin{bmatrix}0&0&12\\2&0&0\\0&0&0\end{bmatrix}$ |

四个未启用方向 $L\to K$、$K\to B$、$B\to L$ 和 $B\to K$ 的 schema、template 和 instance coupling 均为 0。

## 5. 活跃方向的耦合明细

以下明细使用 reachable-context scope（可达上下文范围）。

| 激活条件 | direction | coupled schemas / total | schema proportion | coupled templates / total | template proportion | $M$ / total instances | instance proportion |
| --- | --- | --- | ---: | --- | ---: | --- | ---: |
| `key_gates_location` 或 `combined` | $K\to L$ | 2 / 4 | 0.500000 | 2 / 20 | 0.100000 | 2 / 144 | 0.013889 |
| `location_gates_beef` 或 `combined` | $L\to B$ | 2 / 2 | 1.000000 | 12 / 12 | 1.000000 | 12 / 12 | 1.000000 |

$K\to L$ 中的两个 schemas 是 `left` 和 `right`，对应双向门的两条具体位置模板。$L\to B$ 中的两个 schemas 是 `cook` 和 `cut`，它们展开为 12 条具体 Beef templates。因此两个方向虽然都有 schema count 2，但 template count 分别为 2 和 12。

## 6. 最短路径统计

| anchor | 最短路径数 | $N_{K\to L}$ range | $N_{L\to B}$ range | $D$ range |
| --- | ---: | --- | --- | --- |
| `independent` | 75600 | [0, 0] | [0, 0] | [2, 9] |
| `key_gates_location` | 30240 | [1, 1] | [0, 0] | [2, 9] |
| `location_gates_beef` | 90 | [0, 0] | [4, 4] | [5, 8] |
| `combined` | 56 | [1, 1] | [4, 4] | [5, 8] |

路径范围的含义如下：

- `key_gates_location` 和 `combined` 的每条最短路径都穿过一次受钥匙控制的门，因此 $N_{K\to L}=[1,1]$；
- `location_gates_beef` 和 `combined` 的每条最短路径都执行两次 `cook` 和两次 `cut`，因此 $N_{L\to B}=[4,4]$；
- Beef 功能区限制把动作域最小切换次数从 2 提高到 5；
- 四个任务的 $L^*$ 相同，但约束越多，可用的最短动作排列越少，最短路径数从 75600 依次降到 30240、90 和 56。

`MDP/show_factored_mdp.py` 还验证了 `independent` 中的一条 10 步完成路径：

```text
up -> right -> right -> down
-> head-white -> tail-white
-> cook -> cook -> cut -> cut
```

该路径最终到达 $((2,2),(2,2),(2,2))$，未折扣总奖励为 $-10$。它只是一个合法代表；上表的范围来自 shortest-path DAG（最短路径有向无环图）中的全部最短路径，而不是这一条示例路径。

## 7. 动作可用性与分支因子

统计范围为全部非终止可达状态。

| anchor | 合法动作总数 | Mean Location actions | Mean Key actions | Mean Beef actions | Mean branching | Branching range |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `independent` | 4533 | 2.224 | 2.668 | 1.335 | 6.227 | [3, 10] |
| `key_gates_location` | 3597 | 2.184 | 2.546 | 1.336 | 6.066 | [3, 9] |
| `location_gates_beef` | 3669 | 2.224 | 2.668 | 0.148 | 5.040 | [3, 9] |
| `combined` | 2913 | 2.184 | 2.546 | 0.182 | 4.912 | [3, 8] |

钥匙门主要减少 Location 动作和部分可达 Location–Key 组合。Beef 功能区限制不会减少 `location_gates_beef` 的可达状态数，但会显著降低 Beef 动作在任意位置的平均可用性。因此 $L^*$ 匹配不代表四个任务具有相同的分支结构。

## 8. PI/VI 交叉验证

| anchor | PI/VI 最大价值差 | 策略动作差异状态数 | 无法由并列最优解释的差异 |
| --- | ---: | ---: | ---: |
| `independent` | 0 | 402 | 0 |
| `key_gates_location` | 0 | 357 | 0 |
| `location_gates_beef` | 0 | 442 | 0 |
| `combined` | 0 | 357 | 0 |

四个 anchors 中，Policy Iteration（策略迭代，PI）与 Value Iteration（价值迭代，VI）在全部可达状态上的价值一致。策略动作不同的状态均属于并列最优动作的不同选择，不是价值求解错误。

## 9. 可视化结果

绘图脚本正常运行时，对 `combined` 环境执行一次 VI：

```text
VI on 'combined': 13 iterations, 594 reachable states
```

生成的结果为：

- [三因子图](figures/week3_three_factor_graph.png)：三张 component graphs，以及双向钥匙门、kitchen-cook 和 board-cut 规则；
- [联合价值切片](figures/week3_joint_value_slices.png)：固定 Beef 为 $(0,0)$、$(1,1)$、$(2,2)$ 时的 $V^*(l,k\mid b)$；灰色 `x` 表示不可达联合状态，终止状态价值为 0；
- [Anchor 对比图](figures/week3_anchor_comparison.png)：四个 anchors 的 $S/K$、$N$、$D$ 和 $L^*$。

每张图同时保存了 SVG 版本。

## 10. 当前结果的解释边界

当前任务族已经匹配状态因子规模、初始状态、目标、原语代价和最优路径长度，并且只激活 $K\to L$ 与 $L\to B$ 两类方向性耦合。

仍需保留以下限制：

- `key_gates_location` 和 `combined` 只有 594 个可达状态，另外两个 anchors 有 729 个；
- 四个 anchors 的最短路径数量差异很大；
- 平均合法动作数和分支因子没有匹配；
- Beef gate 同时改变路径耦合次数和动作域切换范围；
- 当前结果描述确定性环境的任务结构，不构成人类采用三因子表示的行为证据。

因此，后续比较学习者或人类行为时，不能只用 $L^*$ 宣称任务难度已经完全匹配。可达状态、最短路径数量、分支因子和动作域切换都需要作为独立的 nuisance differences（干扰差异）报告。
