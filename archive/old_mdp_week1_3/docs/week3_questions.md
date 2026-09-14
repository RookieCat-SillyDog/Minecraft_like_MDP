# 第三周思考题

联合状态记为

$$
x=(l,k,b), \qquad c=(k,b), \qquad x=(l,c).
$$

两种写法指向同一个联合状态。后续分析保留 $k$ 与 $b$ 的独立结构，并以从初始状态出发实际可达的联合状态图为准。

## 1. 为什么 $(l,k,b)$ 是 Markov state，而只使用 $l$、$k$ 或 $b$ 通常不是？

Markov state（马尔可夫状态）要求：给定当前状态和动作后，下一状态、即时奖励、合法动作与终止条件不再依赖更早的历史。$(l,k,b)$ 包含本环境所有转移规则和终止谓词会读取的变量，因此满足这一要求。

单独使用一个因子会遗漏规则需要的信息。位置相同而钥匙状态不同，穿门动作可能一边可用、一边不可用；牛肉状态相同而位置不同，`cook` 可能只在厨房可用。只观察 $l$、$k$ 或 $b$ 时，同一观测可能对应不同的合法动作或后继状态，通常不满足 Markov 性质。

## 2. 为什么 $c=(k,b)$ 仍然有用？为什么它不能替代对 $k$ 与 $b$ 的显式分解？

$c=(k,b)$ 可以把“位置以外的对象状态”写成一个 context（条件上下文），便于比较同一位置转移在不同对象状态下是否保持不变，也兼容 $x=(l,c)$ 的层级表达。

但 $c$ 不能被当作不可分解的 81-state inventory graph（81 状态物品图）。钥匙动作只改变 $k$，牛肉动作只改变 $b$；第一版依赖也分别表现为 $K\to L$ 和 $L\to B$。显式分解才能识别这种稀疏方向依赖，并把钥匙转移复用到不同牛肉状态、把牛肉转移复用到不同钥匙状态。$c$ 是书写和分组方式，不是对 $k$ 与 $b$ 内部结构的替代。

## 3. 为什么完整环境只有一张 joint-state graph？为什么 $\mathcal L$、$\mathcal K$、$\mathcal B$ 不能直接作为三个互斥 clusters？

环境中的一个节点必须是完整的 Markov 状态 $(l,k,b)$，一条实际转移也发生在两个完整状态之间，因此完整环境只有一张 joint-state graph（联合状态图）$G_{\mathcal X}$。三张 factor graph 描述的是可以复用的分量转移规律，不是三套彼此独立的环境状态。

$\mathcal L$、$\mathcal K$、$\mathcal B$ 是同一节点的三个坐标空间。一个联合状态同时拥有一个位置、一个钥匙状态和一个牛肉状态，不能只属于其中一组。若把三个因子直接当作互斥 clusters（簇），就无法表示 $(l,k,b)$ 的组合，也无法说明某条位置转移是在什么钥匙和牛肉 context 下发生的。正确的 clusters 必须是联合状态集合，并由同一张联合图上的 partition（划分）产生。

## 4. 如何从同一 joint graph 构造 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$？为什么同一 transition 在不同 partitions 下可能具有不同类别？

从 BFS 得到的可达联合状态中，固定其余两个因子，只让目标因子变化：

$$
\begin{aligned}
\mathcal C^L_{k,b}&=\{(l,k,b):l\in\mathcal L\},\\
\mathcal C^K_{l,b}&=\{(l,k,b):k\in\mathcal K\},\\
\mathcal C^B_{l,k}&=\{(l,k,b):b\in\mathcal B\}.
\end{aligned}
$$

这些非空可达 clusters 分别组成 $\Pi^L$、$\Pi^K$ 和 $\Pi^B$。它们是对同一节点集的三种划分，不会生成三张新环境图。

Internal、boundary 和 cross-cluster 是相对于指定 partition 的边分类。同一条钥匙转移只改变 $k$：在 $\Pi^K$ 下，它的两个端点位于同一 cluster，随后再由端点是否为 boundary state（边界状态）判为 internal 或 boundary；在固定 $k$ 的 $\Pi^L$ 和 $\Pi^B$ 下，它会进入另一个 cluster，属于 cross-cluster transition（跨簇转移）。所以边的类别不是边本身的永久标签，报告时必须同时注明使用的 partition。

## 5. “把状态写成三个坐标”和“跨 context 共享 component transition”有什么区别？

写成 $(l,k,b)$ 只是对联合状态进行坐标分解，本身不产生经验共享。Flat joint representation（平坦联合表示）也可以使用三元组索引，却仍为每个联合状态分别学习转移。

跨 context 共享 component transition（分量转移）是一项额外的结构假设：某个因子的转移规律在其他因子的不同取值下保持相同。例如，一条钥匙模板若不依赖 $l$ 和 $b$，便能在多个 $(l,b)$ context 中复用。遇到钥匙门或功能区时，共享需要由少量方向性条件规则修正。前者回答“状态怎样表示”，后者回答“哪些转移知识能够迁移”。

## 6. 分别给出 $K\to L$ 和 $L\to B$ 的例子。哪个 factor 是条件，哪个 factor 被动作改变？

$K\to L$ 的例子是双向钥匙门。钥匙状态 $k$ 是条件因子，门的可执行性读取钥匙谓词；穿门动作改变位置 $l$，而 $k$ 与 $b$ 不变。

$L\to B$ 的例子是功能区限制。位置 $l$ 是条件因子，`cook` 要求位于厨房，`cut` 要求位于切菜板；动作改变牛肉状态 $b$，而 $l$ 与 $k$ 不变。记号 $i\to j$ 的左侧是转移规律读取的条件因子，右侧是动作所属并被改变的目标因子。

## 7. 为什么两个厨房不应把 $K_{L\to B}$ 从 1 变成 2？Template count 与 context multiplicity 分别反映什么复杂度？

Transition template（转移模板）的身份由

$$
e_B=(b,a_B,b')
$$

决定，不包含厨房位置。若两个厨房都允许同一条 $b_{\mathrm{raw}}\xrightarrow{\mathrm{cook}}b_{\mathrm{cooked}}$，抽象规则仍只有一条，所以 $K_{L\to B}=1$；这条规则分别在两个位置 context 中合法实例化，因此 $M_{L\to B}=2$。

Template count（模板计数）$K$ 反映有多少种不同的因子内规则需要另一因子作为条件。Context multiplicity（上下文多重性）$M$ 反映这些规则在多少个条件状态中实际可执行。把两个厨房计成两个 templates，会把“同一规则出现两次”误写成“两种不同规则”。

## 8. 为什么同名 `cook` 可能对应多个 transition templates？

动作名称不是模板的完整标识。模板还包含源牛肉状态和目标牛肉状态：

$$
e_B=(b,\mathrm{cook},b').
$$

例如 $(0,b_d)\xrightarrow{\mathrm{cook}}(1,b_d)$ 与 $(1,b_d)\xrightarrow{\mathrm{cook}}(2,b_d)$ 的源、目标不同，因此是两条模板；不同 $b_d$ 下的源、目标也不同。当前 Beef 图中，两个烹饪阶段与三个切割等级组合为 6 条 `cook` templates。只按动作名聚合会保留一个 schema，却丢失阶段化转移结构。

## 9. Lynn et al. 的 cross-cluster edge 与本任务的 cross-factor conditioning 有什么区别？

Cross-cluster edge（跨簇边）描述一条实际联合图边相对于指定 partition 的拓扑位置：若该边改变了 partition 固定的 context，就从一个 cluster 进入另一个 cluster。它是逐边、逐 partition 的分类。

Cross-factor conditioning（跨因子条件依赖）比较的是 factor-$j$ 分量模板在不同 factor-$i$ context 下的可执行性或结果是否变化。它是跨 contexts 比较转移规律得到的方向性属性。前者问“这条联合边是否跨簇”，后者问“这条分量规则是否依赖另一个因子”；两者衡量的对象不同，不能合并成一个计数。

## 10. 为什么 key-gated movement 可以是 $\Pi^L$ cluster 内部的 movement edge，同时仍构成 $K\to L$ coupling？

在 $\Pi^L$ 中，每个 cluster 固定 $(k,b)$、只允许 $l$ 变化。穿门动作只改变 $l$，所以它的起点和终点仍在同一个 location cluster 中；依照端点是否为 boundary state，它属于 internal 或 boundary transition，而不是 cross-cluster transition。

不过，这条位置模板是否存在会随固定的钥匙状态 $k$ 改变：满足钥匙谓词的 location cluster 有这条边，不满足的 cluster 没有。不同 $\Pi^L$ clusters 的内部位置拓扑因此不同，这正是 $K\to L$ coupling（耦合）。同簇边与跨因子耦合并不矛盾。

## 11. Template proportion 与 instance proportion 中，哪个更接近抽象规则数量，哪个更接近实际经验暴露频率？

Template proportion（模板比例）

$$
\rho^{\mathrm{template}}_{i\to j}=\frac{K_{i\to j}}{|E_j|}
$$

更接近抽象规则层面的复杂度：它表示全部 factor-$j$ templates 中，有多少比例需要 factor-$i$ 条件。

Instance proportion（实例比例）

$$
\rho^{\mathrm{instance}}_{i\to j}
=
\frac{M_{i\to j}}
{\sum_{e_j\in E_j}|\{s_i:e_j\text{ 在 }s_i\text{ 下合法实例化}\}|}
$$

更接近环境提供的经验暴露机会：它表示全部可执行 factor-$i$ context instances 中，耦合模板占多少比例。不过它仍不是智能体在某条轨迹上的真实访问频率；实际路径使用次数由 $N_{i\to j}(\tau)$ 描述。两个比例的分母不同，不能用一个未限定的 `coupling_proportion` 代替。

## 12. 为什么 $S_{K\to L}=S_{L\to B}=2$，但 $K_{K\to L}$ 与 $K_{L\to B}$ 不相等？

Schema count（动作模式计数）$S$ 按唯一动作名称计数。钥匙门控制 `left`、`right` 两种位置动作，功能区控制 `cook`、`cut` 两种牛肉动作，所以两个方向的 $S$ 都等于 2。

Template count $K$ 按有向三元组 $(s_j,a_j,s'_j)$ 计数。双向钥匙门只对应两条位置模板，因此 $K_{K\to L}=2$。`cook` 和 `cut` 各自跨多个牛肉源状态与目标状态展开，各有 6 条模板，因此 $K_{L\to B}=12$。相同的动作类别数不意味着相同的具体规则数。

## 13. 环境中存在一扇钥匙门，但所有最短路径都避开它。它是否增加 structural coupling？是否增加该 query 的 required coupling？

若这扇门在 BFS 可达联合图上形成了随钥匙状态变化的可执行位置模板，它会增加 structural coupling（结构耦合）：对应的动作 schema 和有向 templates 进入 $S_{K\to L}$ 与 $K_{K\to L}$。若门只存在于配置声明中，却在该 anchor 的可达范围内从未形成实际转移，则不能计入当前 reachable-scope 的结构统计，配置层理论计数需要另行报告。

题设中所有最短路径都避开门，因此该 query 的 required coupling（必需耦合）不增加：

$$
\mathcal R_{K\to L}(q)=[0,0].
$$

这说明环境可以具有一条结构依赖，而当前问题的任何最优解都不必使用它。

## 14. 为什么比较 coupling complexity 时必须单独控制最优 primitive 路径长度 $L^*$？

最优 primitive 路径长度（原语路径长度）$L^*$ 本身会影响任务难度。路径越长，执行动作、遇到耦合规则和切换动作域的机会通常越多；在逐步成本和折扣回报下，长度还直接影响价值。

若两个 anchors 的 $L^*$ 不同，行为差异无法明确归因于耦合复杂度还是额外步数。比较时应匹配或统计控制 $L^*$，再分析结构耦合、路径必需耦合与动作域切换。即使 $L^*$ 相等，也仍需报告最短路径数量、可达状态数等其他潜在差异。

## 15. 存在多条同长度最优路径时，为什么不能只报告 PI 或 VI 按 tie-breaking 选出的一条？

PI 或 VI 可以得到正确的最优价值，但在多个动作价值并列时，提取出的单条路径取决于动作顺序和 tie-breaking（并列处理）规则。该路径只是最优解集合中的一个成员。

不同的等长最优路径可能使用不同次数的钥匙门、功能区规则或动作域切换。只报告一条会把实现选择误当作任务属性。应在 shortest-path DAG（最短路径有向无环图）上枚举或动态统计所有最短路径，并报告

$$
\mathcal R_{i\to j}(q)
=
\left[
\min_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau),
\max_{\tau\in\mathcal T^*(q)}N_{i\to j}(\tau)
\right]
$$

以及 $D(\tau)$ 的范围。这样结果不依赖某次并列选择。

## 16. 怎样设计 held-out $(l,k,b)$ recombination，区分 flat、object-separated 和 sparse three-factor learner？

Held-out recombination（留出重组）应确保测试阶段不引入新的单因子节点、动作、模板或耦合谓词，只留出某些从未共同出现的 $(l,k,b)$ 组合。训练暴露次数、奖励、目标和 $L^*$ 需要匹配，避免把熟悉度或路径长度当成表示差异。

一类测试只重组彼此独立的已学分量转移。Flat learner（平坦学习者）没有见过完整联合状态组合，预期迁移较差；能够复用对象分量的学习者应更好。另一类测试把训练中出现过的 $K\to L$ 或 $L\to B$ 规则放入新的无关因子组合，例如在未见过的 $b$ 下使用同一钥匙门。若 object-separated learner（对象分离学习者）只拆分对象状态却没有显式方向性门控，它可能通过独立重组，却无法系统迁移条件规则；sparse three-factor learner（稀疏三因子学习者）应能同时复用分量模板和少量耦合规则。

判别依据不是单个条件的成功率，而是三类模型对同一组留出组合给出的样本外选择与学习曲线预测。具体预测仍取决于 object-separated 模型是否允许额外学习门控，模型定义需要预先固定。

## 17. 构造一个断连 factor graph，说明规则枚举为什么可能包含 BFS 实际无法到达的 joint states

保留钥匙图的 9 个理论节点，但删除所有进入 $k=(2,2)$ 的有向边，并从另一个钥匙状态开始。此时 $(2,2)$ 仍在配置节点表中，却无法从初始状态到达。

直接对三个节点表做笛卡尔积仍会枚举

$$
9\times9\times9=729
$$

个联合状态，其中钥匙为 $(2,2)$ 的 81 个状态都是不可达组合。若其余 8 个钥匙状态以及全部位置、牛肉状态均可达，BFS 只得到

$$
9\times8\times9=648
$$

个联合状态。规则允许某个组合存在，不等于该组合能从指定初始状态到达；结构分析、clusters 和 context 计数都应以 BFS 可达图为默认口径。

## 18. 哪些结果会削弱“人会分别抽象 location、key 与 beef”的假设？

分因子抽象预测：人在单因子转移和耦合规则已学会后，应能迁移到未见过的 $(l,k,b)$ 重组。若训练覆盖、暴露次数和 $L^*$ 得到控制后，这种重组优势仍稳定缺失，假设会受到削弱。

更直接的反例包括：错误和反应时主要由完整联合状态是否见过解释；改变与当前转移无关的因子，造成的干扰与改变目标因子一样大；flat 或不可分解的 $c=(k,b)$ 模型在样本外选择、学习曲线和反应时上持续优于 object-separated 与 sparse three-factor 模型。

单次不显著结果不能单独否定假设，因为训练不足、样本量小或测量不敏感也会产生空结果。更有力的证据应来自预先规定的多个重组条件：因子级迁移反复缺失，同时替代模型稳定给出更好的样本外预测。
