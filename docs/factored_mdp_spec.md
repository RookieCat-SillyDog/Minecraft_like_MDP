# 三因子 Factored MDP 规格

本文规定三因子环境的状态、转移、配置和耦合分析口径。Day 11–12 建立环境与可达状态，Day 13–15 使用同一套定义分析四个 anchors。本文只描述规范；文中列出的预期值必须由实现另行验证。

## 1. Notation table

| 对象 | 记号 | 定义 | 状态数 |
| --- | --- | --- | ---: |
| Location factor | $l=(l_x,l_y)\in\mathcal L$ | $l_x,l_y\in\{0,1,2\}$ | 9 |
| Key factor | $k=(k_h,k_t)\in\mathcal K$ | $k_h,k_t\in\{0,1,2\}$ | 9 |
| Beef factor | $b=(b_c,b_d)\in\mathcal B$ | $b_c,b_d\in\{0,1,2\}$ | 9 |
| Hierarchical context | $c=(k,b)\in\mathcal C$ | $\mathcal C=\mathcal K\times\mathcal B$ | 81 |
| Joint state | $x=(l,k,b)=(l,c)\in\mathcal X$ | $\mathcal X=\mathcal L\times\mathcal K\times\mathcal B$ | 729 |

$x=(l,c)$ 与 $x=(l,k,b)$ 表示同一状态。代码采用后者，保留 Key 与 Beef 的独立结构。任务书使用 $(l_x,l_y)$；代码为兼容已有网格环境，将同一位置存为 `(row, col)=(l_y,l_x)`，绘图坐标再映射为 $(x,y)=(col,row)$。数值状态与展示标签分离；环境只读取配置中的节点、有向边、动作和 predicate（条件谓词）。

耦合分析使用以下记号：

| 对象 | 记号 | 定义 |
| --- | --- | --- |
| 可达联合状态图 | $G_{\mathcal X}$ | 以实际可达的 $x=(l,k,b)$ 为节点的有向转移图 |
| 因子划分 | $\Pi^j$ | 固定另外两个因子、只改变因子 $j$ 得到的 cluster partition |
| 因子 $j$ 的模板集合 | $E_j$ | 全部唯一的确定性有向三元组 $(s_j,a_j,s'_j)$ |
| 有向转移模板 | $e_j=(s_j,a_j,s'_j)$ | 因子 $j$ 内的源状态、动作和目标状态规则 |
| 耦合指示量 | $z_{i\to j}(e_j)$ | 模板 $e_j$ 的可执行性或结果是否随因子 $i$ 改变 |
| 结构耦合数 | $K_{i\to j}$ | 受因子 $i$ 条件控制的唯一 factor-$j$ 模板数 |
| Context 实例数 | $M_{i\to j}$ | Coupled templates 在 factor-$i$ context 中的合法实例化次数 |
| 路径使用次数 | $N_{i\to j}(\tau)$ | 轨迹 $\tau$ 实际执行 coupled factor-$j$ template 的次数 |
| 最优原语长度 | $L^*(q)$ | Query $q$ 的最短动作数 |
| 动作域切换 | $D(\tau)$ | 相邻动作在 $L$、$K$、$B$ 三个 domain 之间的切换次数 |

## 2. 三张 factor graphs

三张 factor graph（因子图）均由节点、动作、有向 transition template（转移模板）和展示标签组成。动作名称全局唯一，每个动作只属于一个因子。对因子 $j$，模板的正式定义为

$$
e_j=(s_j,a_j,s'_j)\in E_j.
$$

因此，模板不是动作类别：相同动作从不同源状态出发，或产生不同目标状态时，属于不同模板；反方向转移也属于另一个模板。同一个 $(s_j,a_j,s'_j)$ 在多个联合状态 context 中出现时仍只计一次。动作不可用表示模板在该 context 中未实例化，不创建失败 self-loop，也不把 $\bot$ 作为目标状态。

按该定义，当前三张确定性 factor graph 的每条唯一有向边都是一个模板：

$$
|E_L|=20,\qquad |E_K|=24,\qquad |E_B|=18.
$$

完整联合状态中的具体转移是模板在某个 context 下的实例。模板可以跨 context 复用，但不能仅按 up、heat、cooking 或 cutting 等动作名称或语义类别合并。

### 2.1 Location

Location 使用 $3\times3$ 四邻接网格，删除两组墙边后保留 10 组双向连接。

```text
          col=0      col=1        col=2

row=0    (0,0) ─── (0,1)   │    (0,2)
            │          │              │
row=1    B(1,0) ─── C(1,1)  D    (1,2)
            │          │              │
row=2 START(2,0) ─── (2,1) │ GOAL(2,2)
```

`B` 是 cutting board（案板），`C` 是 kitchen（灶台），`D` 是候选门边，`│` 表示墙。

$$
W=\bigl\{\{(0,1),(0,2)\},\ \{(2,1),(2,2)\}\bigr\},
\qquad
e_D=\{(1,1),(1,2)\}.
$$

$$
\mathcal A_L=\{\text{up},\text{down},\text{left},\text{right}\}.
$$

Location 与 `env/minecraft.py` 一致，程序中的状态写作 `(row, col)=(l_y,l_x)`，原点在左上角。`up/down` 分别令 row 减/加 1，`left/right` 分别令 column 减/加 1。该存储顺序不改变数学状态空间 $\mathcal L$；越界、撞墙或门条件不成立的动作不合法。

墙永久删除边，不产生跨因子依赖。门边始终属于基础图；启用门控时，两个方向都要求 $k=(2,2)$。通过门只改变 $l$，不改变或消耗 $k$。

### 2.2 Key

Key 的两个维度是一把钥匙的 head 与 tail 属性。

| 数值 | 标签 |
| ---: | --- |
| 0 | `blank` |
| 1 | `black` |
| 2 | `white` |

| 动作 | 结果 | 合法条件 |
| --- | --- | --- |
| `head-black` | $(1,k_t)$ | $k_h\ne1$ |
| `head-white` | $(2,k_t)$ | $k_h\ne2$ |
| `tail-black` | $(k_h,1)$ | $k_t\ne1$ |
| `tail-white` | $(k_h,2)$ | $k_t\ne2$ |

首版没有恢复为 `blank` 的动作；从 $(0,0)$ 可达全部 9 个 Key 状态。门谓词为

$$
g_D(k)=\mathbf 1[k_h=2\land k_t=2].
$$

### 2.3 Beef

| 维度 | 0 | 1 | 2 |
| --- | --- | --- | --- |
| cooking $b_c$ | `raw` | `medium` | `cooked` |
| processing $b_d$ | `whole` | `sliced` | `minced` |

| 动作 | 结果 | 合法条件 |
| --- | --- | --- |
| `heat` | $(b_c+1,b_d)$ | $b_c<2$ |
| `cool` | $(b_c-1,b_d)$ | $b_c>0$ |
| `chop` | $(b_c,1)$ | $b_d=0$ |
| `stir` | $(b_c,2)$ | $b_d=1$ |

cooking 轴可逆，processing 轴首版单向。功能区固定为

$$
l_{board}=(1,0),
\qquad
l_{kitchen}=(1,1).
$$

Beef 的位置谓词必须绑定到具体的有向模板，而不是绑定到整个动作名称或 cooking、cutting 语义类别。为保留首版 $K_{L\to B}=2$ 的 anchor，配置需要预先指定且只指定两条受控模板：

$$
e_{\mathrm{kitchen}}
=
(b^{\mathrm{cook}}_{\mathrm{src}},a_{\mathrm{cook}},b^{\mathrm{cook}}_{\mathrm{dst}}),
$$

$$
e_{\mathrm{board}}
=
(b^{\mathrm{cut}}_{\mathrm{src}},a_{\mathrm{cut}},b^{\mathrm{cut}}_{\mathrm{dst}}).
$$

第一条只在 kitchen 实例化，第二条只在 board 实例化；其余 Beef templates 必须对 Location 保持不变。两条模板的具体源状态、动作和目标状态必须作为 task configuration 的显式设计变量，并在确定后固定。若将所有 `heat/cool` 和 `chop/stir` 边分别绑定到功能区，则按 $(s_B,a_B,s'_B)$ 定义会有多于两个 coupled templates，不满足 $K_{L\to B}=2$。Key 与 Beef 从初始状态起已经存在，地图不设置拾取点。

### 2.4 联合状态图、因子划分与状态抽象

环境只有一张可达联合状态图 $G_{\mathcal X}$。三张 factor graph 描述可以跨 context 复用的 component transition law，不是三组彼此分离的联合状态节点。

对同一张 $G_{\mathcal X}$，固定另外两个因子并改变目标因子，得到三种 cluster：

$$
C^L_{k,b}=\{(l,k,b):l\in\mathcal L\},
$$

$$
C^K_{l,b}=\{(l,k,b):k\in\mathcal K\},
$$

$$
C^B_{l,k}=\{(l,k,b):b\in\mathcal B\}.
$$

它们分别组成 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$。将状态写成 $(l,k,b)$ 只是 Markov state（马尔可夫状态）的坐标分解；只有当不同 context 下的联合状态共享相同 component transition law 时，才构成本文所说的 state abstraction（状态抽象）。

Internal、boundary 和 cross-cluster transition 是相对于某个 $\Pi^j$ 对联合图边的位置分类。方向性耦合则比较对应 cluster 内的 factor-$j$ 拓扑是否随 context 改变，两者不能互相替代。例如，钥匙门的移动边可以位于 location cluster 内部，但它在不同 Key context 下可执行性不同，所以仍贡献 $K\to L$ 耦合。

## 3. 联合 MDP

四个 anchors 共用

$$
x_0=((2,0),(0,0),(0,0)),
$$

$$
G(l,k,b)=\mathbf 1[l=(2,2)\land k=(2,2)\land b=(2,2)].
$$

合法动作集合与转移为

$$
\mathcal A(x)=\mathcal A_L(x)\cup\mathcal A_K(x)\cup\mathcal A_B(x),
$$

$$
\begin{aligned}
F((l,k,b),a_L)&=(F_L(l,a_L;k),k,b),\\
F((l,k,b),a_K)&=(l,F_K(k,a_K),b),\\
F((l,k,b),a_B)&=(l,k,F_B(b,a_B;l)).
\end{aligned}
$$

首版只允许 $K\to L$ 和 $L\to B$；$L\to K$、$K\to B$、$B\to L$ 与 $B\to K$ 必须为 0。每个动作只改变所属因子。

合法动作必须存在对应边、改变目标因子、满足已启用谓词，且当前状态不是 terminal state（终止状态）。每个合法非终止动作奖励为 $-1$，$\gamma=0.95$。终止状态没有合法动作，价值为 0；非法动作不表示为失败 self-loop（自环）。

### 3.1 表示假设与环境边界

完整的 $(l,k,b)$ 是环境进行 Markov prediction 所需的状态，但它不规定学习者必须怎样组织经验。本环境为以下四种统计共享假设提供共同测试基础：

- Flat joint representation：分别估计每个联合状态的转移，经验不自动跨 $(l,k,b)$ 组合迁移。
- Single-factor abstraction：只共享 Location、Key 或 Beef 中一张 component graph，其余因子作为 context。
- Object-separated abstraction：将 Key 与 Beef 保留为不同状态空间，使二者的知识可以分别跨另一对象状态迁移。
- Sparse three-factor representation：共享三张 component graph，只额外存储少量方向性 coupling rules。

当前环境和分析不实现这些 learner，也不把 PI、VI 的一致性解释为认知模型证据。下一阶段通过 held-out $(l,k,b)$ recombination 比较零样本迁移：训练保留 component transition 证据，但留出部分联合组合。表示假设由迁移与错误位置区分；$L^*$、path coupling 和动作域切换描述规划需求，不能单独识别学习表示。

## 4. BFS 可达状态

`states` 必须从 $x_0$ 出发，按固定动作顺序调用实际 `actions` 与 `transitions` 执行 BFS（广度优先搜索），不能直接枚举 729 个组合。

BFS 必须保证：

- 每个声明状态均可从 $x_0$ 合法到达；
- 每个声明状态的合法后继仍属于 `states`；
- 断连因子图不会产生虚假联合状态；
- 同一配置得到稳定的枚举顺序。

理论状态数 729 与实际可达状态数分别报告。断连测试可删除某个 Key 状态的全部入边，验证包含该状态的联合状态不会被声明为可达。

## 5. Task configuration

环境只解释配置，不根据任务名或展示标签执行专用逻辑。配置至少包含：

| 配置项 | 内容 |
| --- | --- |
| `task_name` | 任务标识 |
| `location_graph` | Location 节点、动作、有向边、标签与绘图坐标 |
| `key_graph` | Key 节点、动作、有向边、标签与绘图坐标 |
| `beef_graph` | Beef 节点、动作、有向边、标签与绘图坐标 |
| `blocked_location_edges` | 从 Location 基础网格删除的墙边 |
| `location_landmarks` | 起点、目标、案板和灶台的位置标记 |
| `edge_landmarks` | 候选门边等边标记 |
| `location_gates` | 受 Key predicate 控制的精确 Location template ID 或 $(s_L,a_L,s'_L)$ |
| `beef_gates` | 受 Location predicate 控制的精确 Beef template ID 或 $(s_B,a_B,s'_B)$ |
| `template_ids` | 三张图中每个唯一有向三元组的稳定标识；不得只使用动作类别作为模板标识 |
| `initial_state` | $x_0$ |
| `terminal_predicate` | $G(x)$ |
| `query_set` | 用于四个 anchors 匹配 $L^*$ 的预先固定起点-终止 query 集合 |
| `primitive_costs` | 首版均为 1 |
| `action_order` | BFS、求解和绘图共用的固定顺序 |
| `discount_factor` | 折扣因子，首版为 0.95 |

标签和绘图坐标不是 `FactoredTaskConfig` 的独立字段，而是分别保存在三个 `FactorGraph` 的 `labels` 与 `coordinates` 中。由于三张图本身属于任务配置，这仍满足数值状态、语义标签和通用转移代码相互分离的要求。

固定动作顺序为：

```text
up, down, left, right,
head-black, head-white, tail-black, tail-white,
heat, cool, chop, stir
```

现有 `env/minecraft.py`、`env/mdp.py`、Policy Evaluation、PI 和 VI 保持不变。新环境实现既有 `MDP` 接口。

## 6. Anchors 与长度预期

四个 anchors 共用三张基础图、墙、门边、功能区、$x_0$、目标、动作成本和动作顺序，只切换跨因子谓词。

| Anchor | $K_{K\to L}$ | $K_{L\to B}$ | 规则 |
| --- | ---: | ---: | --- |
| `independent` | 0 | 0 | Location 不读 Key；Beef 不读 Location |
| `key_gates_location` | 2 | 0 | 双向门要求 $k=(2,2)$ |
| `location_gates_beef` | 0 | 2 | 两条预先指定的 Beef 有向模板分别绑定 kitchen 与 board |
| `combined` | 2 | 2 | 同时启用两类谓词 |

从 $(2,0)$ 到 $(2,2)$ 的最短移动长度为 4，有两条 Location 最短路径：一条经过 board、kitchen 和门，另一条经过 kitchen 和门但跳过 board。Beef 初始状态 $(0,0)$ 的两条合法出边恰好是受控的 `heat` 与 `chop` templates，因此每条解都必须在 kitchen 或 board 执行其中之一；两种选择各自都能结合一条长度为 4 的 Location 路径。Key 目标需要 2 个动作，Beef 目标需要 4 个动作，因此四个 anchors 的设计预期为

$$
L^*=4+2+4=10.
$$

分析器和测试已重新验证四个 anchors 的 query 可行性与 $L^*$ matching；结果均为 $L^*=10$，其余运行结果见第 8 节。该长度来自当前拓扑和固定 query，不是由模板定义单独推出的结论。

## 7. Coupling 计数说明

### 7.1 结构耦合

令 $i$ 为条件因子，$j$ 为转移规律被改变的因子。对每条 $e_j\in E_j$ 定义

$$
z_{i\to j}(e_j)=
\begin{cases}
1, & \text{只改变因子 }i\text{ 时，模板的可执行性或结果发生变化},\\
0, & \text{否则}.
\end{cases}
$$

比较两个 context 时，除因子 $i$ 外的其他条件必须相同。一个 context 中动作存在、另一个 context 中动作被省略，属于可执行性变化；同一个 $(s_j,a_j)$ 在不同 factor-$i$ context 中产生不同 $s'_j$，属于结果变化。若出现两个不同目标状态，相应的两个有向三元组分别进入 $E_j$，并分别标记为 coupled。

结构耦合数为

$$
K_{i\to j}
=
\left|
\left\{
e_j\in E_j:z_{i\to j}(e_j)=1
\right\}
\right|.
$$

$K_{i\to j}$ 统计唯一的 coupled factor-$j$ templates，不统计动作名称、条件值数量、联合状态实例或路径执行次数。结构矩阵的行是条件因子，列是转移规律被改变的因子：

$$
\mathbf K_{\mathrm{struct}}
=
\begin{pmatrix}
0 & K_{L\to K} & K_{L\to B}\\
K_{K\to L} & 0 & K_{K\to B}\\
K_{B\to L} & K_{B\to K} & 0
\end{pmatrix}.
$$

双向钥匙门对应两个不同方向的 Location templates，所以目标值 $K_{K\to L}=2$。在 $|E_B|=18$ 的定义下，要得到 $K_{L\to B}=2$，必须只有两条具体 Beef templates 受 Location 控制。此时 template proportion 是 $2/18$，不是按 cooking、cutting 两个动作类别计算的 $2/2$。

### 7.2 Context 实例数与两种比例

结构模板数与这些模板出现于多少个条件 context 是两个量。定义

$$
M_{i\to j}
=
\sum_{e_j:z_{i\to j}(e_j)=1}
\left|
\left\{
s_i:e_j\text{ 在 }s_i\text{ 下合法实例化}
\right\}
\right|.
$$

报告必须区分

$$
\rho^{\mathrm{template}}_{i\to j}
=
\frac{K_{i\to j}}{|E_j|}
$$

与

$$
\rho^{\mathrm{instance}}_{i\to j}
=
\frac{M_{i\to j}}
{\displaystyle
\sum_{e_j\in E_j}
\left|
\left\{
s_i:e_j\text{ 在 }s_i\text{ 下合法实例化}
\right\}
\right|}.
$$

前者描述 factor-$j$ 规则集中有多少比例需要 factor-$i$ 条件；后者描述具体可执行的 factor-$i$ context 实例中有多少比例属于 coupled templates。不得使用未注明分母的 coupling proportion。$M_{i\to j}$ 不是完整联合状态转移数量，也不额外乘以与该方向无关的第三个因子。

结构分析默认使用该 anchor 的可达联合状态图所支持的 context。若需要同时报告配置层面的理论计数，必须另设 analysis scope，并使用不同字段名，不能与 reachable-context count 混合。

### 7.3 Query 级使用次数

对轨迹

$$
\tau=(x_0,a_1,x_1,\ldots,a_T,x_T),
$$

第 $t$ 步的 factor-$j$ template 为

$$
e_{j,t}=(s_{j,t-1},a_t,s_{j,t}).
$$

路径实际使用 $i\to j$ coupled template 的次数为

$$
N_{i\to j}(\tau)
=
\sum_{t=1}^{T}
\mathbf 1[a_t\in\mathcal A_j]\,
z_{i\to j}(e_{j,t}).
$$

动作必须属于被影响因子 $j$，并且该步使用的模板满足 $z_{i\to j}=1$，该步才贡献 1。获得钥匙的 Key action 不计入 $N_{K\to L}$；实际执行受钥匙控制的 Location template 才计入。同一模板被重复执行时按次数重复计数，所以 $N_{i\to j}(\tau)$ 可以小于、等于或大于 $K_{i\to j}$。

令 $\mathcal T^*(q)$ 为 query $q$ 的全部最短轨迹，必须报告

$$
\mathcal R_{i\to j}(q)
=
\left[
\min_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau),
\max_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau)
\right].
$$

结构中存在但未被任何最短路径使用的 gate 会增加 $K_{i\to j}$，但该 query 的相应范围仍可为 $[0,0]$。当前实现使用

$$
e_{\mathrm{kitchen}}=((0,0),\texttt{heat},(1,0)),
\qquad
e_{\mathrm{board}}=((0,0),\texttt{chop},(0,1)).
$$

前者只在 kitchen、后者只在 board 实例化。二者是 $b=(0,0)$ 的全部合法出边，因此固定 query 的每条最短路径都至少使用其中一条；`location_gates_beef` 与 `combined` 的 $\mathcal R_{L\to B}$ 均为 $[1,1]$。这表示每条最短解确实需要一次 Location-conditioned Beef transition，但不需要两条都使用。

动作域切换继续独立定义为

$$
D(\tau)
=
\sum_{t=1}^{T-1}
\mathbf 1[m(a_t)\ne m(a_{t+1})].
$$

对所有最短路径报告 $\mathcal R_D(q)$ 的 min-max 范围。$L^*$、$\mathcal R_{i\to j}$ 和 $\mathcal R_D$ 不合并成加权分数；四个 anchors 先匹配 $L^*$，再比较耦合与切换需求。

### 7.4 分析输出字段

每个非对角方向至少规划以下结构字段：

| 字段 | 含义 |
| --- | --- |
| coupled_templates | $K_{i\to j}$ |
| total_templates | $|E_j|$ |
| coupled_instances | $M_{i\to j}$ |
| total_instances | Instance proportion 的分母 |
| template_proportion | $\rho^{\mathrm{template}}_{i\to j}$ |
| instance_proportion | $\rho^{\mathrm{instance}}_{i\to j}$ |
| analysis_scope | reachable_contexts 或明确命名的理论范围 |

每个 query 另行记录 optimal_length、各活跃方向的 path_coupling_range、switch_range、最短路径数量和可达状态数。字段设计只规定数据含义，不代表当前实现已经产生或验证这些数值。

## 8. Day 11–12 验收与后续边界

- 三张因子图各有 9 个节点，且 $|E_L|=20$、$|E_K|=24$、$|E_B|=18$；
- 同一状态和动作的合法性、转移及奖励不读取路径历史；
- 每类动作只改变所属因子；
- 无效动作不出现在 `actions(state)` 中；
- 终止状态没有动作，合法转移概率和为 1；
- BFS 满足可达性、后继闭合性、断连排除和稳定顺序；
- `independent` 不含跨因子依赖；
- 通用配置保留 `location_gates` 和 `beef_gates`，在 `independent` 中二者均为空；
- 环境代码不包含任务名或展示标签分支；
- 既有 48 项测试继续通过。

旧版 Day 13–14 曾记录以下结果：

1. 钥匙门同时要求 $k_h=2$ 与 $k_t=2$，通过门时只改变 $l$。
2. cooking 只在 kitchen 可用，cutting 只在 board 可用，动作只改变 Beef 的对应维度。
3. 旧计数口径下，四个 anchors 的结构耦合矩阵与原目标表一致。
4. shortest-path DAG 能够在不保存全部路径的情况下计算路径数量、耦合范围和动作域切换范围。
5. 旧配置下四个 anchors 的 $L^*$ 均为 10；最短路径数依次记录为 75600、30240、180 和 60。
6. PI 与 VI 在每个环境的全部可达状态上价值一致，不同策略动作可由并列最优解释。

这些历史结果不是新口径的验证证据。尤其是第 2、3、5 项使用了按 cooking、cutting 动作类别合并模板的旧设计，不能直接证明新的 $(s_j,a_j,s'_j)$ 计数满足 $K_{L\to B}=2$。

已完成的实现同步：

1. `DirectedTransition` 本身即是 template，稳定展示 ID 从三元组派生；三张图的模板数为 $20/24/18$。
2. 配置固定上述两个精确 Beef templates，因而 `location_gates_beef` 与 `combined` 均有 $K_{L\to B}=2$。
3. 分析器在 reachable-context scope 下枚举六个非对角方向、保持第三因子不变地比较转移结果，输出 $z$ 导出的 $K$、$M$、两种比例和总实例数。
4. `query_set` 首版固定为 $(x_0,)$；四个 anchors 都重新求解，$L^*=10$ 保持匹配。

新口径下的验证结果如下：

| anchor | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $\mathcal R_{K\to L}$ | $\mathcal R_{L\to B}$ | $\mathcal R_D$ | reachable states | shortest paths |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| `independent` | 0 | 0 | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 |
| `key_gates_location` | 2 | 0 | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 |
| `location_gates_beef` | 0 | 2 | 10 | [0, 0] | [1, 1] | [3, 9] | 729 | 10800 |
| `combined` | 2 | 2 | 10 | [1, 1] | [1, 1] | [3, 9] | 594 | 4068 |

在激活方向上，$M_{K\to L}=2$、总可执行实例数为 144；$M_{L\to B}=2$、总可执行实例数为 146。因此 template proportion 分别为 $2/20$ 和 $2/18$，instance proportion 分别为 $2/144$ 和 $2/146$。其余四个非对角方向均为 0。PI 与 VI 在全部可达状态的价值差均为 0，策略差异均可由并列最优动作解释。
