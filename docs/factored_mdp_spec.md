# 三因子 Factored MDP 规格

本文规定 Day 11–12 的状态、转移、配置与测试。耦合分析和其余 anchors 属于 Day 13–15。

## 1. Notation table

| 对象 | 记号 | 定义 | 状态数 |
| --- | --- | --- | ---: |
| Location factor | $l=(l_x,l_y)\in\mathcal L$ | $l_x,l_y\in\{0,1,2\}$ | 9 |
| Key factor | $k=(k_h,k_t)\in\mathcal K$ | $k_h,k_t\in\{0,1,2\}$ | 9 |
| Beef factor | $b=(b_c,b_d)\in\mathcal B$ | $b_c,b_d\in\{0,1,2\}$ | 9 |
| Hierarchical context | $c=(k,b)\in\mathcal C$ | $\mathcal C=\mathcal K\times\mathcal B$ | 81 |
| Joint state | $x=(l,k,b)=(l,c)\in\mathcal X$ | $\mathcal X=\mathcal L\times\mathcal K\times\mathcal B$ | 729 |

$x=(l,c)$ 与 $x=(l,k,b)$ 表示同一状态。代码采用后者，保留 Key 与 Beef 的独立结构。任务书使用 $(l_x,l_y)$；代码为兼容已有网格环境，将同一位置存为 `(row, col)=(l_y,l_x)`，绘图坐标再映射为 $(x,y)=(col,row)$。数值状态与展示标签分离；环境只读取配置中的节点、有向边、动作和 predicate（条件谓词）。

## 2. 三张 factor graphs

三张 factor graph（因子图）均由节点、动作、有向边和展示标签组成。动作名称全局唯一，每个动作只属于一个因子。首版有向边数为

$$
|E_L|=20,\qquad |E_K|=24,\qquad |E_B|=18.
$$

### 2.1 Location

Location 使用 $3\times3$ 四邻接网格，删除两组墙边后保留 10 组双向连接。

```text
          col=0      col=1        col=2

row=0    (0,0) ─── (0,1)   │    (0,2)
            │          │              │
row=1    (1,0) ─── B(1,1)  D    C(1,2)
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
l_{board}=(1,1),
\qquad
l_{kitchen}=(1,2).
$$

启用 $L\to B$ 时，`heat/cool` 只在 kitchen 可用，`chop/stir` 只在 board 可用；未启用时，Beef 动作不读取 $l$。Key 与 Beef 从初始状态起已经存在，地图不设置拾取点。

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
| `location_gates` | 受 Key 允许状态集合控制的 Location 边 |
| `beef_gates` | 受 Location 允许状态集合控制的 Beef 边 |
| `initial_state` | $x_0$ |
| `terminal_predicate` | $G(x)$ |
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
| `location_gates_beef` | 0 | 2 | cooking 与 processing 分别绑定功能区 |
| `combined` | 2 | 2 | 同时启用两类谓词 |

Day 11–12 只实现 `independent`。其中候选门边是普通边，案板和灶台不限制 Beef 动作。

从 $(2,0)$ 到 $(2,2)$ 的最短移动长度为 4，且存在两条 Location 最短路径；两条都经过案板、门和灶台。Key 目标需要 2 个动作，Beef 目标需要 4 个动作，因此四个 anchors 的设计预期为

$$
L^*=4+2+4=10.
$$

该结果是手工推算，必须由后续最短路径分析验证。

## 7. Coupling 计数说明

任务书要求按有向 transition template 计数，并明确给出四个 anchors 的目标值：双向门使 $K_{K\to L}=2$，两类功能区限制使 $K_{L\to B}=2$。本文以 anchor 表中的矩阵项为目标，不把任务书中含义不明且与 Key 状态重名的“首版令 $k=2$”实现为额外配置参数。

当前 Beef 图包含两组功能区规则、四种动作和 18 条实例化有向边，因此“转移模板总数”和 coupling proportion（耦合比例）的分母仍需在 Day 13 统一定义。Day 11–12 不实现非零耦合分析；配置只需保留规则、条件状态和受控有向边所需的结构。`independent` 的所有非对角项均为 0，不受计数分母影响。

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

以下内容不计入 Day 11–12 的完成状态，进入 Day 13 后再实现和验证：

1. 实例化钥匙门谓词，并验证它同时要求 $k_h=2$ 与 $k_t=2$，通过门时只改变 $l$。
2. 实例化厨房和案板规则，并验证它们分别只改变 $b_c$ 与 $b_d$。
3. 统一 transition template 的计数层级和耦合比例分母，再实现非零结构耦合矩阵。
