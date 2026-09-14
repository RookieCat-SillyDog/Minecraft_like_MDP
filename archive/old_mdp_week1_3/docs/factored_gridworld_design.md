# Factored GridWorld：Coupling × Representation × Search

## 1. 研究问题

固定客观路线成本后，研究：

\[
\boxed{\text{sparse cross-factor coupling}
\rightarrow \text{policy sensitivity / replanning footprint}
\rightarrow \text{online search demand}}
\]

进一步检验 learned representation 是否调节上述关系。

---

## 2. MDP 定义

定义确定性 shortest-path MDP：

\[
M=(\mathcal S,\mathcal A,T,c,\mathcal G).
\]

### 状态空间

\[
s=(l,k,b),\qquad \mathcal S=L\times K\times B.
\]

\[
L=\{0,1,2\}\times\{0,1,2\},\quad |L|=9,
\]

\[
K=\{\text{Blank},\text{ShallowBlue},\text{Blue}\},
\]

\[
B=\{\text{Raw},\text{Medium},\text{Well}\}.
\]

因此：

\[
|\mathcal S|=9\times3\times3=81.
\]

任务：把 `Well` beef 带到 Goal `G`。

\[
\mathcal G=\{(G,k,\text{Well}):k\in K\}.
\]

### 动作

```text
up / down / left / right
dye
cook
```

每个 primitive action 成本均为：

\[
c(s,a)=1.
\]

目标：最小化到达 \(\mathcal G\) 的总 action cost。

---

## 3. Transition grammar 与 coupling

### 3.1 Location transition

令 \(E\) 为 3×3 grid 中所有 Manhattan-neighbor edges。

Door **不是 location/state**，而是一条特殊边：

\[
e_D=\{l_i,l_j\}\in E.
\]

普通边：

\[
(l,k,b)\xrightarrow{move}(l',k,b),\qquad \{l,l'\}\in E,\ \{l,l'\}\neq e_D.
\]

Door edge：

\[
(l,k,b)\xrightarrow{move}(l',k,b)
\iff
\{l,l'\}=e_D\ \land\ k=\text{Blue}.
\]

因此：

\[
\boxed{K\rightarrow L}
\]

因为 Key state 改变 Location transition 是否可执行。

### 3.2 Key transition

`dye` 在所有 location 均可执行：

\[
\text{Blank}\rightarrow\text{ShallowBlue}\rightarrow\text{Blue}.
\]

因此基础任务中**没有** \(L\rightarrow K\)。

### 3.3 Beef transition

设 Kitchen 为 \(C\)。只有在 \(C\) 可执行 `cook`：

\[
\text{Raw}\rightarrow\text{Medium}\rightarrow\text{Well}.
\]

\[
cook\in\mathcal A(s)\iff l=C.
\]

因此：

\[
\boxed{L\rightarrow B}.
\]

基础 dependency graph：

\[
\boxed{K\rightarrow L\rightarrow B}.
\]

---

## 4. 两张 3×3 地图

两张地图使用完全相同的：

- state/action space；
- Start、Kitchen、Goal；
- reward/cost；
- grid connectivity；
- coupling rules。

只改变 **Door edge 的位置**。

公共位置：

\[
S=(0,0),\qquad C=(0,1),\qquad G=(2,1).
\]

所有未标记的相邻节点均正常双向连接。

### Map A：Low coupling leverage

Door edge：

\[
e_D^A=\{(0,0),(0,1)\}=\{S,C\}.
\]

```text
y=2   (0,2) ─── (1,2) ─── (2,2)
         │          │          │
y=1     C  ───── (1,1) ─────  G
        ║D          │          │
y=0     S  ───── (1,0) ───── (2,0)

        x=0        x=1        x=2
```

`D` 标记的是 `S-C` 之间的 edge，不占格子。

Door route：

```text
dye → dye → Door(S→C) → cook → cook → R → R
```

\[
C_D(s_0)=7.
\]

Bypass route：

```text
R → U → L → cook → cook → R → R
```

\[
C_B(s_0)=7.
\]

因此：

\[
\boxed{\Delta C(s_0)=C_D-C_B=0}.
\]

### Map B：High coupling leverage

Door edge：

\[
e_D^B=\{(0,1),(1,1)\}.
\]

```text
y=2   (0,2) ─── (1,2) ─── (2,2)
         │          │          │
y=1     C  ══D══ (1,1) ─────  G
         │          │          │
y=0     S  ───── (1,0) ───── (2,0)

        x=0        x=1        x=2
```

Door route：

```text
U → cook → cook → dye → dye → Door(C→1,1) → R
```

\[
C_D(s_0)=7.
\]

Bypass route：

```text
U → cook → cook → D → R → R → U
```

\[
C_B(s_0)=7.
\]

因此同样：

\[
\boxed{\Delta C(s_0)=0}.
\]

两张地图 baseline objective cost 完全相同；区别是 Door coupling 对整个 optimal policy 的影响范围不同。

---

## 5. VI / PI 的作用

VI/PI 只作为 oracle，计算 ground-truth：

\[
V^*(s)=\min_{a\in\mathcal A(s)}\left[1+V^*(T(s,a))\right],
\]

终点：

\[
V^*(s)=0,\qquad s\in\mathcal G.
\]

定义 optimal-action set：

\[
\Pi^*(s)=\arg\min_{a\in\mathcal A(s)}
\left[1+V^*(T(s,a))\right].
\]

VI/PI 解决“最优解是什么”；研究指标描述“coupling 使 optimal policy 改变了多少”。

---

## 6. 计算指标

### 6.1 Route tradeoff

定义：

\[
\Delta C(s)=C_D(s)-C_B(s),
\]

其中：

- \(C_D\)：约束路径至少使用一次 Door edge；
- \(C_B\)：约束路径禁止使用 Door edge。

Baseline 控制：

\[
\boxed{\Delta C(s_0)=0}.
\]

它是 **cost control**，不是 difficulty 指标。

### 6.2 Key-induced policy discontinuity

令：

\[
\Omega=\{(l,b): (l,\text{Blank},b)\notin\mathcal G\}.
\]

定义：

\[
D_K=
\frac{1}{|\Omega|}
\sum_{(l,b)\in\Omega}
\mathbf 1
\left[
\Pi^*(l,\text{Blank},b)
\neq
\Pi^*(l,\text{Blue},b)
\right].
\]

含义：改变 Key factor 后，有多少 spatial/task states 的 optimal action set 发生变化。

在上述规则下：

\[
D_K^A=\frac{5}{26}\approx0.192,
\]

\[
D_K^B=\frac{21}{26}\approx0.808.
\]

### 6.3 Door coupling leverage

定义 counterfactual MDP \(M^{-D}\)：规则完全相同，但 Door edge 永久删除。

对 \(K=\text{Blue}\) 定义：

\[
\Gamma_D(l,b)=
V^*_{M^{-D}}(l,\text{Blue},b)
-
V^*_M(l,\text{Blue},b).
\]

\(\Gamma_D>0\) 表示该 joint state 的最优规划实际受 Door coupling 帮助。

平均 leverage：

\[
\bar\Gamma_D=
\frac{1}{|\Omega|}
\sum_{(l,b)\in\Omega}\Gamma_D(l,b).
\]

Coupling footprint：

\[
F_D=
\frac{1}{|\Omega|}
\sum_{(l,b)\in\Omega}
\mathbf 1[\Gamma_D(l,b)>0].
\]

两张地图：

\[
\bar\Gamma_D^A=\frac{4}{26}\approx0.154,
\qquad
F_D^A=\frac{2}{26}\approx0.077.
\]

\[
\bar\Gamma_D^B=\frac{46}{26}\approx1.769,
\qquad
F_D^B=\frac{19}{26}\approx0.731.
\]

因此两张地图满足：

\[
\Delta C_A(s_0)=\Delta C_B(s_0)=0,
\]

但：

\[
D_K^B\gg D_K^A,
\qquad
\bar\Gamma_D^B\gg\bar\Gamma_D^A.
\]

这才是两张地图的理论差异。

### 6.4 Replanning footprint

对 perturbation \(p\) 得到新 MDP \(M_p\)，例如：

- Door blocked；
- Door moved；
- Start changed。

定义：

\[
R_p=
\sum_{s}\mu(s)
\mathbf 1
\left[
\Pi_M^*(s)\neq\Pi_{M_p}^*(s)
\right].
\]

\(\mu(s)\) 可取 uniform distribution，或实验实际 start-state distribution。

含义：一次局部变化使多大范围的已有 policy 失效。

### 6.5 Online search effort

所有 representation model 使用同一 search：

\[
f(n)=g(n)+\omega h_R(n).
\]

只允许 learned representation 改变 heuristic \(h_R\)；search implementation、queue discipline、tie-breaking 固定。

记录：

\[
N_{expand},\quad route,\quad switch,\quad planning\ RT.
\]

结构指标 \(D_K,\Gamma_D,R_p\) 不是 human difficulty 本身；它们是 planning-demand predictors。

---

## 7. 绘图

### Figure 1：Physical task graph

画 3×3 spatial nodes 与所有 edges：

- Door 画在 edge 上；
- 标记 `S / C / G`；
- 旁边画 dependency graph：

\[
K\rightarrow L\rightarrow B.
\]

### Figure 2：Joint-state Policy Atlas

画成：

```text
                    K
           Blank   ShallowBlue   Blue
B = Raw      3×3       3×3        3×3
B = Medium   3×3       3×3        3×3
B = Well     3×3       3×3        3×3
```

每个 3×3 panel 中画：

- \(\Pi^*(s)\) 的方向箭头；
- `DYE` / `COOK`；
- Door open/closed；
- 多个 optimal actions 时同时显示。

比较不同 K columns，直接高亮 policy flip。

### Figure 3：Coupling-leverage heatmap

对每个 Beef state 画一个 3×3 heatmap：

\[
\Gamma_D(l,b).
\]

颜色越强，表示 Door coupling 对该位置的 optimal cost 影响越大。

预期：

- Map A：高亮区域很小；
- Map B：高亮区域覆盖明显更广。

### Figure 4：Replanning map

perturbation 前后比较：

\[
\mathbf 1[\Pi_M^*(s)\neq\Pi_{M_p}^*(s)].
\]

把发生 policy change 的 states 高亮，即可直接看到 replanning footprint。

---

## 8. 计算流程

```text
1. 枚举 81 joint states
2. 构造 T(s,a)
3. VI/PI → V*(s), Π*(s)
4. constrained shortest path → CD, CB, ΔC
5. 比较 Blank vs Blue → DK
6. 构造 M^{-D} → ΓD, FD
7. 构造 probe M_p → Rp
8. 用固定 online search → Nexpand / route / switch / RT prediction
9. 画 Policy Atlas + leverage/replanning heatmaps
```

---

## 9. 当前最小研究比较

核心不是继续堆地图，而是比较一对 cost-matched MDP：

\[
\boxed{
\Delta C_A(s_0)=\Delta C_B(s_0)=0
}
\]

同时：

\[
\boxed{
D_K^A<D_K^B,
\qquad
\bar\Gamma_D^A<\bar\Gamma_D^B.
}
\]

实验问题：在客观路线成本相同的情况下，更大的 coupling-induced policy sensitivity 是否产生更高的 search / replanning demand，以及这种效应是否依赖 learned representation。
