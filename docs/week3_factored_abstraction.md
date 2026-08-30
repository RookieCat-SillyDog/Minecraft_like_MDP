# 第三周任务：三因子 Factored MDP 与耦合复杂度

## 1. 第二周结论与本周边界

第二周任务通过。你已经完成 Minecraft-like MDP、可达状态分析、Policy Iteration（PI）与 Value Iteration（VI）交叉验证，并能够生成价值函数和最优路径图。

第三周不增加新的动态规划算法。本周需要把当前五元状态推广为三个彼此对应的 $3\times3$ factor spaces，并把 factor 之间的耦合定义成可以由程序计算和验证的量。

本周暂不实现：

- Reward Machine；
- Successor Representation；
- state、temporal 或 hierarchical RL learner；
- Weighted A*；
- 人类行为拟合与参数估计。

这些内容只有在三因子环境、复杂度指标和 matched task anchors 验证完成后才进入下一阶段。

## 2. Notation 与科学问题

### 2.1 三个对应的状态空间

完整状态写为

$$
x=(l,k,b)
\in
\mathcal X
=\mathcal L\times\mathcal K\times\mathcal B.
$$

三个 factor 分别为：

$$
l=(l_x,l_y)\in\mathcal L,
$$

$$
k=(k_h,k_t)\in\mathcal K,
$$

$$
b=(b_c,b_d)\in\mathcal B.
$$

每个 factor 都是 $3\times3$ state space：

$$
|\mathcal L|=|\mathcal K|=|\mathcal B|=9,
\qquad
|\mathcal X|=9^3=729.
$$

具体语义为：

| Factor | 第一维 | 第二维 | 状态数 |
| --- | --- | --- | ---: |
| Location $l$ | $l_x\in\{0,1,2\}$ | $l_y\in\{0,1,2\}$ | 9 |
| Key $k$ | key-head attribute $k_h\in\{0,1,2\}$ | key-tail attribute $k_t\in\{0,1,2\}$ | 9 |
| Beef $b$ | cooking level $b_c\in\{0,1,2\}$ | cutting level $b_d\in\{0,1,2\}$ | 9 |

数值标签必须与通用 MDP 分离。绘图时可以把 key levels 映射为三种颜色，把 beef levels 映射为 `raw/medium/cooked` 和 `whole/sliced/minced`。

为保留上一版 location-context 表达，可以定义

$$
c=(k,b)\in\mathcal C=\mathcal K\times\mathcal B,
\qquad
x=(l,c)=(l,k,b).
$$

但代码和分析不能把 key 与 beef 合并成一个不可分解的 81-state inventory graph。

完整环境只有一张从 initial state 出发可达的 joint-state transition graph：

$$
\mathcal G_{\mathcal X}=(\mathcal X_{mathrm{reach}},\mathcal E_{mathcal X}).
$$

Location、key 和 beef 是每个 joint state 的三个坐标，不是三组互斥节点。针对不同的 abstraction hypothesis，需要在同一张 joint graph 上构造三种 partition：

$$
\begin{aligned}
\mathcal C^L_{k,b}
&=\{(l,k,b):l\in\mathcal L\},\\
\mathcal C^K_{l,b}
&=\{(l,k,b):k\in\mathcal K\},\\
\mathcal C^B_{l,k}
&=\{(l,k,b):b\in\mathcal B\}.
\end{aligned}
$$

这些 clusters 的集合分别记作 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$。例如，$\Pi^L$ 中的每个 cluster 都固定 $(k,b)$，并包含一份可达的 location graph。Partition 是对 abstraction hypothesis 的形式化，不会产生新的环境状态。

### 2.2 本周科学问题

完整的 $(l,k,b)$ 保证任务满足 Markov property，但人不一定把 729 个 joint states 分别学习。需要区分：

1. **Flat joint representation**：分别学习每个 $(l,k,b)$。
2. **Single-factor abstraction**：只复用 location、key 或 beef 中的一张 component graph。
3. **Object-separated abstraction**：把 key 与 beef 作为不同 state spaces，而不是合并为一个 inventory graph。
4. **Sparse three-factor representation**：学习三张 component graphs 和少量 directional coupling rules。

本周不实现这些认知 learner，但环境和输出必须支持下一阶段的 held-out recombination 比较。

## 3. 开始任务前的思考题

在编码前创建 `docs/week3_questions.md`，用自己的语言回答以下问题，并准备口头解释。

1. 为什么 $(l,k,b)$ 是 Markov state，而只使用 $l$、$k$ 或 $b$ 通常不是？
2. 为什么 $c=(k,b)$ 仍然有用？为什么它不能替代对 $k$ 与 $b$ 的显式分解？
3. 为什么完整环境只有一张 joint-state graph？为什么 $\mathcal L$、$\mathcal K$、$\mathcal B$ 不能直接作为三个互斥 clusters？
4. 如何从同一 joint graph 构造 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$？为什么同一 transition 在不同 partitions 下可能具有不同类别？
5. “把状态写成三个坐标”和“跨 context 共享 component transition”有什么区别？
6. 分别给出 $K\to L$ 和 $L\to B$ 的例子。哪个 factor 是条件，哪个 factor 被动作改变？
7. 为什么两个厨房不应把 $K_{L\to B}$ 从 1 变成 2？Template count 与 context multiplicity 分别反映什么复杂度？
8. 为什么同名 `cook` 可能对应多个 transition templates？
9. Lynn et al. 的 cross-cluster edge 与本任务的 cross-factor conditioning 有什么区别？
10. 为什么 key-gated movement 可以是 $\Pi^L$ cluster 内部的 movement edge，同时仍构成 $K\to L$ coupling？
11. Template proportion 与 instance proportion 中，哪个更接近抽象规则数量，哪个更接近实际经验暴露频率？
12. 为什么 $K_{K\to L}=2$ 与 $K_{L\to B}=2$ 即使数量相同，也不是相同的 task manipulation？
13. 环境中存在一扇钥匙门，但所有最短路径都避开它。它是否增加 structural coupling？是否增加该 query 的 required coupling？
14. 为什么比较 coupling complexity 时必须单独控制最优 primitive 路径长度 $L^*$？
15. 存在多条同长度最优路径时，为什么不能只报告 PI 或 VI 按 tie-breaking 选出的一条？
16. 怎样设计 held-out $(l,k,b)$ recombination，区分 flat、object-separated 和 sparse three-factor learner？
17. 构造一个断连 factor graph，说明规则枚举为什么可能包含 BFS 实际无法到达的 joint states。
18. 哪些结果会削弱“人会分别抽象 location、key 与 beef”的假设？

## 4. MDP 与代码接口

### 4.1 必须沿用现有框架

- [ ] 保留 `env/minecraft.py` 的第二周实现，不重写或替换。
- [ ] 不修改 `algorithms/policy_evaluation.py`、`policy_iteration.py` 和 `value_iteration.py`。
- [ ] 新环境继续实现 `env/mdp.py` 中的统一 `MDP` 接口。
- [ ] 若认为现有接口不足，先写出最小反例并讨论，再进行最小修改。

建议新增：

```text
env/
├── factored_minecraft.py
└── factored_tasks.py

experiments/
├── analyze_factored_tasks.py
└── plot_factored_tasks.py

tests/
└── test_factored_minecraft.py
```

### 4.2 三类动作与转移

动作分为三个互斥 domain：

$$
\mathcal A(x)
=\mathcal A_L(x)
\cup\mathcal A_K(x)
\cup\mathcal A_B(x).
$$

每个 primitive action 只能改变一个 factor：

$$
F((l,k,b),a_L)
=\left(F_L(l,a_L;k,b),k,b\right),
$$

$$
F((l,k,b),a_K)
=\left(l,F_K(k,a_K;l,b),b\right),
$$

$$
F((l,k,b),a_B)
=\left(l,k,F_B(b,a_B;l,k)\right).
$$

第一版 task family 固定以下 sparse dependency：

$$
F_L(l,a_L;k,b)=F_L(l,a_L;k),
$$

$$
F_K(k,a_K;l,b)=F_K(k,a_K),
$$

$$
F_B(b,a_B;l,k)=F_B(b,a_B;l).
$$

因此第一版只允许：

- key state 改变 location transition，即 $K\to L$；
- location 改变 beef transition，即 $L\to B$。

以下 coupling 在第一版必须为 0：

$$
K_{L\to K},
K_{K\to B},
K_{B\to L},
K_{B\to K}.
$$

其他固定规则：

- [ ] 不可执行动作从 `actions(state)` 中排除，不表示为失败 self-loop。
- [ ] 每个非终止 primitive action 的奖励为 $-1$，折扣因子为 $\gamma=0.95$。
- [ ] terminal state 没有合法动作，价值为 0。
- [ ] key、beef 和颜色名称都来自 task configuration，不得写入通用 transition code。

### 4.3 通用 task configuration

配置至少包含：

- location、key 和 beef 三张有向 component graphs；
- 每个 factor 的绘图坐标和语义标签；
- location transition 上的 key predicates；
- beef transition 上的 location predicates；
- initial joint state 与 terminal predicate；
- task name、primitive costs 和用于复现实验的固定 action order。

不得出现 `if task_name == "beef"`、`if color == "red"` 一类任务语义硬编码。通用环境只执行配置提供的 graph、predicate 和 transition rule。

### 4.4 必须使用真正的 BFS

`states` 必须由 initial state 出发，沿实际 `actions` 与 `transitions` 执行 breadth-first search 得到，不能仅枚举 $9^3$ 个理论组合。

BFS 至少保证：

- [ ] 每个声明状态都有一条从 initial state 出发的合法路径。
- [ ] 每个声明状态的全部合法 successors 也在 `states` 中。
- [ ] 断连的 location、key 或 beef 区域不会产生虚假的 reachable joint states。
- [ ] 枚举顺序稳定，使测试和图形结果可重复。

## 5. Joint graph、cluster topology 与 coupling complexity

### 5.1 同一 joint graph 上的三种 cluster partitions

Complexity analyzer 必须从 BFS 得到的 reachable joint-state graph 构造 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$，不能分别生成三套环境。

相对于指定 partition $\Pi^j$：

- **Boundary state**：至少存在一个合法动作会改变当前 partition 固定的 context $s_{-j}$。
- **Internal transition**：起点与终点在同一 cluster，并且两个端点都不是 boundary state。
- **Boundary transition**：起点与终点仍在同一 cluster，但至少一个端点是 boundary state。
- **Cross-cluster transition**：改变 $s_{-j}$，从 $\mathcal C^j_{s_{-j}}$ 进入另一个 cluster。

三类 transition 在给定 partition 下必须互斥且完备。同一 joint transition 在不同 partitions 下允许得到不同类别。因此每次报告 internal、boundary 或 cross-cluster 时，都必须同时报告使用的是 $\Pi^L$、$\Pi^K$ 还是 $\Pi^B$。

这一分类借鉴 Lynn et al. 对 modular network 中 internal、boundary 与 cross-cluster edges 的区分。Lynn 的指标描述一条边在指定 partition 中的拓扑位置；本任务的 directional coupling 描述不同 context clusters 中 component transition law 是否相同。不得把两者合并成一个计数。

### 5.2 Transition template

令 $\mathcal E_j$ 为 factor $j$ 的全部唯一有向 transition templates。确定性环境中的一个模板定义为

$$
e_j=(s_j,a_j,s'_j).
$$

稳定 template ID 必须使用 `(source_factor_state, action, target_factor_state)`，计数规则为：

- [ ] 不得只按 action name 聚合。
- [ ] 同名 action 对应不同 source-target pairs 时，分别计数。
- [ ] 同一个 source-action-target rule 在多个 contexts 中出现时，仍是一个 template。
- [ ] 动作不可用属于 availability 的变化，但 $\bot$ 不作为正常 target-state template。
- [ ] 调换 task configuration 中 location、context 或 action 的顺序不能改变 template ID。

### 5.3 Directional coupled template count

令 $\mathcal F=\{L,K,B\}$。定义

$$
K_{i\to j}
=
\left|
\left\{
e_j\in\mathcal E_j:
\operatorname{avail}(e_j\mid s_i)
\text{ or }
\operatorname{outcome}(e_j\mid s_i)
\text{ varies with }s_i
\right\}
\right|.
$$

也就是说，$K_{i\to j}$ 统计比较不同 factor-$i$ conditioning contexts 时，有多少种 factor-$j$ component rules 不再保持不变。它不统计 cross-cluster edges。

矩阵的行表示 conditioning factor，列表示 transition 被改变的 factor：

$$
\mathbf K_{\mathrm{struct}}
=
\begin{pmatrix}
0 & K_{L\to K} & K_{L\to B}\\
K_{K\to L} & 0 & K_{K\to B}\\
K_{B\to L} & K_{B\to K} & 0
\end{pmatrix}.
$$

结构耦合计数规则：

- [ ] action availability 或 transition outcome 只要依赖另一 factor，就计入对应矩阵项。
- [ ] 一扇双向钥匙门计为两个 $K\to L$ templates。
- [ ] key-gated movement 改变不同 $\Pi^L$ clusters 中的 internal location topology；不得因此直接把 movement edge 标成 cross-cluster。
- [ ] 自动验证第一版未使用的四个 off-diagonal entries 等于 0。

### 5.4 Context-expanded multiplicity 与两种比例

定义耦合模板在具体 conditioning states 中的实例数：

$$
M_{i\to j}
=
\sum_{e_j:z_{i\to j}(e_j)=1}
\left|
\left\{
s_i:e_j\text{ is instantiated under }s_i
\right\}
\right|.
$$

`instantiated` 表示该模板在 conditioning state $s_i$ 下合法执行并产生模板指定的 target。$M_{i\to j}$ 不替代 $K_{i\to j}$。

必须分别报告：

$$
\rho^{\mathrm{template}}_{i\to j}
=
\frac{K_{i\to j}}{|\mathcal E_j|},
$$

$$
\rho^{\mathrm{instance}}_{i\to j}
=
\frac{M_{i\to j}}
{\displaystyle
\sum_{e_j\in\mathcal E_j}
\left|
\left\{
s_i:e_j\text{ is instantiated under }s_i
\right\}
\right|}.
$$

Template proportion 衡量 factor-$j$ 抽象规则中有多少比例需要 factor-$i$ conditioning。Instance proportion 衡量实际可执行 factor-$j$ transition instances 中，有多少属于这些 coupled templates。两个分母不同，输出和报告中禁止使用没有限定词的 `coupling_proportion`。

**两个厨房示例：**若两个厨房都允许同一个

$$
b_{\mathrm{raw}}
\xrightarrow{\mathrm{cook}}
b_{\mathrm{cooked}},
$$

则 $K_{L\to B}=1$，$M_{L\to B}=2$。若同名 `cook` 还实现

$$
b_{\mathrm{medium}}
\xrightarrow{\mathrm{cook}}
b_{\mathrm{well}},
$$

则这是第二个有向 template；若它也在两个厨房执行，则两个模板合计 $K_{L\to B}=2$，并向 $M_{L\to B}$ 贡献 4 个 instances。

### 5.5 Query-level coupling

对路径 $\tau$ 计算每个 active coupling direction 实际使用的 transition 数：

$$
N_{i\to j}(\tau)
=\sum_{t=1}^{T}
\mathbf 1[a_t\in\mathcal A_j]
z_{i\to j}(e_{j,t}),
\qquad
e_{j,t}=(s_{j,t-1},a_t,s_{j,t}).
$$

对所有最短路径报告：

$$
\mathcal R_{i\to j}(q)
=
\left[
\min_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau),
\max_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau)
\right].
$$

动作 domain 为 $m(a)\in\{L,K,B\}$。切换次数为

$$
D(\tau)
=\sum_{t=1}^{T-1}
\mathbf 1[m(a_t)\neq m(a_{t+1})].
$$

统一输出至少包含：

```text
cluster_topology:
  partition: location | key | beef
  internal_transition_count: int
  boundary_transition_count: int
  cross_cluster_transition_count: int

directional_coupling:
  i_to_j:
    coupled_template_count: int
    total_template_count: int
    template_coupling_proportion: float
    coupled_instance_count: int
    total_instance_count: int
    instance_coupling_proportion: float

optimal_length: int
path_coupling_range:
  k_to_l: [min, max]
  l_to_b: [min, max]
switch_range: [min, max]
reachable_states: int
```

最短路径很多时，应在 shortest-path DAG 上动态计算 min-max，不要求把全部路径保存在内存中。不得只分析 PI 或 VI 返回的一条路径。

## 6. 四个 task anchors

四个条件固定 $|\mathcal L|=|\mathcal K|=|\mathcal B|=9$，并使用相同 initial state、goal、primitive cost 和三张基础 component graphs。首版令 $k=2$：

| Anchor | $K_{K\to L}$ | $K_{L\to B}$ | 其他 coupling | 必须包含的规则 |
| --- | ---: | ---: | ---: | --- |
| `independent` | 0 | 0 | 全部为 0 | 移动不依赖 key；beef transition 不依赖 location |
| `key_gates_location` | 2 | 0 | 全部为 0 | 一扇双向门要求指定 key state |
| `location_gates_beef` | 0 | 2 | 全部为 0 | cook 与 chop 分别要求 kitchen 和 cutting board |
| `combined` | 2 | 2 | 全部为 0 | 同时包含钥匙门和两个功能区限制 |

钥匙门 predicate 必须同时读取 $k_h$ 和 $k_t$。Kitchen 只改变 $b_c$，cutting board 只改变 $b_d$。任何动作都不得同时改变两个 factors。

布局调整顺序：

1. 固定三个 factor graphs、initial state 和 goal。
2. 放置门、kitchen 和 cutting board，计算四个 anchors 的 $L^*$。
3. 调整 gate 或功能区位置，使指定比较中的 $L^*$ 完全相同。
4. 再比较 path coupling 与 switch ranges。
5. 如果不能匹配，报告具体差值和原因；未匹配条件不得标记为完成。

还要报告 action availability、平均 branching factor、reachable-state count 和最短路径数量，用于发现剩余 nuisance differences。

## 7. Milestone 1：Notation、规格与通用环境（Day 11-12）

建议 commit：`week3-m1: specify three-factor mdp`

- [ ] 完成 `docs/week3_questions.md`。
- [ ] 创建 `docs/factored_mdp_spec.md`，第一部分必须是与本任务书一致的 notation table。
- [ ] 写清 $\mathcal L$、$\mathcal K$、$\mathcal B$、$\mathcal C$ 和 $\mathcal X$ 的关系。
- [ ] 写清 $\mathcal G_{\mathcal X}$、$\Pi^L$、$\Pi^K$、$\Pi^B$ 与 $\mathcal C^j_{s_{-j}}$ 的关系。
- [ ] 实现三个通用 $3\times3$ factor graphs 与 task configuration。
- [ ] 实现三类 action，并测试每个 action 只改变一个 factor。
- [ ] 实现真正的 BFS reachable-state enumeration。
- [ ] 实现 `independent` anchor。
- [ ] 添加 Markov state、factor invariance、动作合法性、终止条件和 BFS 测试。
- [ ] 在 `progress/day11.md` 和 `progress/day12.md` 记录工作、问题与 AI 使用。

验收时需要现场解释：为什么 $x=(l,c)=(l,k,b)$ 两种写法都正确，为什么完整环境只有一张 joint graph，以及三种 cluster partitions 如何表达不同 abstraction hypotheses。

## 8. Milestone 2：Coupling matrix 与四个 anchors（Day 13-14）

建议 commit：`week3-m2: analyze three-factor coupling`

- [ ] 从 reachable joint graph 构造 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$。
- [ ] 在每种 partition 下标记 internal、boundary 与 cross-cluster transitions。
- [ ] 实现稳定的有向 transition template ID。
- [ ] 实现完整 $3\times3$ structural coupling matrix。
- [ ] 对每个方向输出 $K_{i\to j}$、$M_{i\to j}$、template proportion 与 instance proportion。
- [ ] 实现四个 anchors，并得到预期的 $K_{K\to L}$ 与 $K_{L\to B}$。
- [ ] 验证其他四个 off-diagonal coupling entries 全为 0。
- [ ] 实现 shortest-path DAG 或等价方法，计算 coupling 与 switch min-max ranges。
- [ ] 调整 task layout，完成指定 query 的 $L^*$ matching。
- [ ] 直接复用现有 PI 和 VI 求解四个环境。
- [ ] 比较全部可达状态上的价值并检查并列最优动作。
- [ ] 在 `progress/day13.md` 和 `progress/day14.md` 记录结果与问题。

分析脚本必须生成以下 query-level summary，并同时输出 Section 5 规定的 cluster-topology 与 directional-coupling records：

| anchor | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $N_{K\to L}$ range | $N_{L\to B}$ range | $D$ range | reachable states | PI/VI max diff |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |

## 9. Milestone 3：可视化、报告与验收（Day 15）

建议 commit：`week3-m3: validate three-factor task family`

生成 PNG 和 SVG 两种格式：

- [ ] `figures/week3_three_factor_graph.*`：并列展示 location、key 和 beef 三张 $3\times3$ 图，并标出 active coupling rules。
- [ ] `figures/week3_joint_value_slices.*`：至少固定 initial、intermediate 和 goal 三个 beef states，分别展示 $V^*(l,k\mid b)$ 的 location-by-key slices。
- [ ] `figures/week3_anchor_comparison.*`：比较四个 anchors 的 structural coupling、path coupling、$D$ 和 $L^*$。
- [ ] 图中数值必须来自分析程序，不得手工填写。
- [ ] 运行绘图时不得出现 glyph 或字体 warning。

创建 `docs/week3_report.md`，不超过 6 页，包含：

- [ ] 第一部分为 notation table；
- [ ] 三因子 MDP 和 hierarchical context $c=(k,b)$；
- [ ] 一张 reachable joint graph 与 $\Pi^L$、$\Pi^K$、$\Pi^B$ 三种 cluster partitions；
- [ ] flat、single-factor、object-separated 与 sparse three-factor hypotheses；
- [ ] internal、boundary、cross-cluster、template coupling、instance multiplicity、query-level coupling、$L^*$ 与 $D$ 的区别；
- [ ] 两个厨房的 worked example，并明确 $K_{L\to B}=1$、$M_{L\to B}=2$；
- [ ] 四个 anchors 的匹配过程和最终结果；
- [ ] PI/VI 一致性与 tie-aware shortest-path 分析；
- [ ] 三张结果图和当前 nuisance differences；
- [ ] 下一阶段的 held-out $(l,k,b)$ recombination 设计。

在 `progress/day15.md` 中记录最终命令、结果、AI 使用和仍不理解的部分。

## 10. 自动测试与完成判定

第三周通过需要同时满足：

- [ ] 第二周已有 48 项测试继续通过。
- [ ] 新测试覆盖三个 factor spaces 和四个 anchors。
- [ ] 每个 location、key、beef action 只改变对应 factor。
- [ ] 门只在 key predicate 满足时提供对应 location action。
- [ ] cook 与 chop 只在要求的位置改变对应 beef dimension。
- [ ] 三张 component graphs 都恰好包含 9 个理论 states。
- [ ] 理论 joint state 数为 729；`states` 仅包含 initial state 实际可达的子集。
- [ ] 至少一个断连测试证明 BFS 不声明不可达 joint states。
- [ ] 从 reachable joint graph 正确构造 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$。
- [ ] 每条 reachable directed transition 在每个指定 partition 下恰好属于 internal、boundary、cross-cluster 三类之一。
- [ ] 对每个 partition，三类 transition count 之和等于全部 reachable directed transitions。
- [ ] 同一 transition 在不同 partitions 下可以得到不同类别，并有明确测试覆盖。
- [ ] 同一 `raw + cook -> cooked` template 配置在两个厨房时，$K_{L\to B}=1$ 且 $M_{L\to B}=2$。
- [ ] 同名 `cook` 对应两个不同 beef source-target pairs 时，template count 为 2。
- [ ] 双向 key-gated door 产生两个有向 $K_{K\to L}$ templates。
- [ ] Key-gated movement 被识别为不同 $\Pi^L$ clusters 中 internal topology 的变化，不被错误计作 cross-cluster movement。
- [ ] Template proportion 与 instance proportion 分别使用 Section 5.4 中规定的分母。
- [ ] 调换 task configuration 中 location、context 或 action 的顺序不改变 template ID 和计数。
- [ ] 四个 anchors 的 coupling matrix 与目标完全一致。
- [ ] 第一版未激活的 coupling entries 均为 0。
- [ ] PI 与 VI 在全部可达状态上的价值差小于 $10^{-8}$。
- [ ] 策略差异均通过 action-value 检查或报告真实错误。
- [ ] coupling 与 switch ranges 不依赖算法 tie-breaking。
- [ ] 指定比较的 $L^*$ 已匹配。
- [ ] README 写明测试、分析、绘图命令和预期输出。
- [ ] 创建 annotated tag `week3-submission`，指向最终验收 commit。

最终现场验收：

1. 不使用 AI，解释 coupling matrix 的行、列和两个 active entries。
2. 临时改变一扇门的 key predicate，先预测 coupling matrix、reachable states 和 $L^*$，再运行验证。
3. 临时把 kitchen constraint 改为 location invariant，预测 $K_{L\to B}$ 如何变化。
4. 构造两条同长度但 action-domain switch 数不同的最优路径，并解释 range。
5. 修改一个 anchor 后，现场补充相应自动测试。

## 11. AI 工具使用要求

允许使用 AI 辅助阅读、排错、测试和绘图，但必须：

- [ ] 在每天的 progress 文件中说明 AI 用于什么问题。
- [ ] 标明 AI 辅助生成的代码、测试和文字。
- [ ] 自己运行并检查生成内容。
- [ ] 能够脱离 AI 解释、修改并测试核心环境和 coupling analysis。

无法解释、无法现场修改或没有经过测试的内容，不计入完成成果。
