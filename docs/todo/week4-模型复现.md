# 王浩全阶段性训练与项目执行计划

# 1. 目标

接下来 3–4 周的重点不是继续开放式地“找地图、调位置、找 complexity metric”，而是通过**定向论文复现 + 边界清晰的实施子任务**建立三个基础能力：

1. **可靠实施**：任务能按时完成，代码可运行、可复现、可解释。
2. **方法理解**：能从论文的 scientific question 推导到 representation、algorithm、experiment 和结果。
3. **迁移能力**：能把论文中的 finite-state task representation / temporal abstraction 迁移到我们当前的 Navigation × Task-FSM 项目。

# 2. 当前课题的统一 computational picture

我们暂时把原来的 Key × Location × Beef joint-state formulation 改写成两个层次。

## 2.1 Navigation state

\[
s_t \in S_{\mathrm{nav}}
\]

描述 agent 当前的空间位置和必要的低层环境信息。

导航地图在不同 task condition 之间原则上保持固定。

## 2.2 Abstract task state

\[
u_t \in U
\]

描述当前任务进行到了哪个抽象阶段，例如：

\[
u_0=\text{nothing acquired}
\]

\[
u_1=\text{key acquired}
\]

\[
u_2=\text{door opened}
\]

\[
u_3=\text{beef acquired}
\]

\[
u_4=\text{cooked}
\]

环境中的 high-level event 通过 labeling function

\[
L:S_{\mathrm{nav}}\rightarrow 2^{\mathcal P}
\]

驱动 task FSM：

\[
u_{t+1}=\delta_u(u_t,L(s_{t+1}))
\]

于是完整 Markov state 可以写成：

\[
(s_t,u_t)\in S_{\mathrm{nav}}\times U
\]

## 2.3 Subtask reward

FSM state \(u_t\) 决定当前应该追求什么 subgoal。

例如：

- \(u_0\)：到达 Key
- \(u_1\)：到达 Door / Workbench
- \(u_2\)：到达 Beef
- \(u_3\)：到达 Kitchen
- \(u_4\)：到达 Goal

因此 task-level representation 不再和地图拓扑混成一个难以解释的大 joint MDP，而是显式作用于固定地图之上。

## 2.4 Temporal abstraction

进一步考虑 FSM 上的 transition sequence：

\[
u_i\rightarrow u_j\rightarrow u_k
\]

如果这一段在很多任务中反复出现，可以把它作为一个 temporally extended chunk：

\[
o=(I_o,\pi_o,\beta_o)
\]

因此后续可以研究：

- 哪一种 FSM topology 更支持 state abstraction？
- 哪一种 task family 中重复 sequence 更支持 temporal abstraction？
- training 中形成的 abstraction 是否会迁移并 bias 后续 planning / search？

---

# 3. 论文阅读与复现顺序

建议分成三个层级，不要求一次把所有经典 HRL 都完整重现。

## Level A：必须完整做最小复现

1. Icarte et al. (2018) — Reward Machines
2. Sutton, Precup & Singh (1999) — Options

## Level B：做针对性复现

3. Andreas, Klein & Levine (2017) — Policy Sketches

## Level C：重点读 representation，可做概念性实现

4. Parr & Russell — Hierarchies of Machines (HAM)

---

# 4. Paper 1 — Reward Machines

## Citation

Rodrigo Toro Icarte, Toryn Q. Klassen, Richard Valenzano, and Sheila A. McIlraith.  
**Using Reward Machines for High-Level Task Specification and Decomposition in Reinforcement Learning.**  
Proceedings of the 35th International Conference on Machine Learning (ICML), PMLR 80:2107–2116, 2018.

## BibTeX

```bibtex
@inproceedings{icarte2018rewardmachines,
  title     = {Using Reward Machines for High-Level Task Specification and Decomposition in Reinforcement Learning},
  author    = {Icarte, Rodrigo Toro and Klassen, Toryn Q. and Valenzano, Richard and McIlraith, Sheila A.},
  booktitle = {Proceedings of the 35th International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {80},
  pages     = {2107--2116},
  year      = {2018},
  publisher = {PMLR}
}
```

## 必须讲清楚的问题

1. 标准 MDP 的 state \(s\) 和 Reward Machine state \(u\) 分别表示什么？
2. high-level proposition / event \(\mathcal P\) 是什么？
3. labeling function
   \[
   L:S\rightarrow 2^{\mathcal P}
   \]
   做什么？
4. Reward Machine
   \[
   \mathcal R=\langle U,u_0,\delta_u,\delta_r\rangle
   \]
   中每个量的含义是什么？
5. 为什么 reward 对原始 environment state history 可以是 non-Markovian，但在
   \[
   S\times U
   \]
   上重新变成 Markovian？
6. QRM 为什么可以对不同 RM states 的 subpolicy 并行做 off-policy update？
7. Reward Machine 和普通 HRL hierarchy 的关键区别是什么？

## 最小复现任务

### A. Environment

自己实现一个最小 OfficeWorld / GridWorld：

- 4-neighbor movement
- wall
- coffee
- mail（可以第二阶段再加）
- office
- forbidden/decorative cell（可选）

不要求一开始复刻作者完整地图。

### B. Event labeling

实现：

```python
def label(state) -> set[str]:
    ...
```

例如：

```text
{coffee}
{office}
{decoration}
{}
```

### C. Reward Machine

至少实现两个 task：

#### Task 1

```text
get coffee -> deliver coffee to office
```

#### Task 2

```text
visit A -> B -> C -> D
```

RM 必须是独立对象，而不是把所有逻辑硬编码在 environment step() 中。

### D. Product MDP

显式构造或隐式计算：

\[
S' = S\times U
\]

并实现 tabular Value Iteration。

### E. 必须产生的一张关键图

固定 navigation position \(s\)，比较不同 RM state \(u\) 下的 optimal policy：

\[
\pi^*(a\mid s,u_1)
\neq
\pi^*(a\mid s,u_2)
\]

这张图是本项目最重要的概念性检查之一。

### F. QRM

实现最小 tabular QRM：

- one Q table per RM state
- environmental transition only执行一次
- 对多个 RM states 做 counterfactual/off-policy update

不要求实现 DQRM。

### G. 对照

至少比较：

```text
standard tabular Q-learning
vs.
QRM
```

不要求完全复现论文所有 learning curve，但应该能说明：

- 两者最终 policy 是否一致；
- sample efficiency 是否有可见差异；
- 为什么会产生差异。

## 不需要做

- 不需要完整复现 WaterWorld。
- 不需要 6-layer DQN。
- 不需要为了追论文曲线做大量 hyperparameter tuning。
- 不需要先读作者代码然后照抄。

## 验收标准

能够不看论文解释：

```text
environment state
event
labeling function
RM state
RM transition
reward transition
product MDP
QRM update
```

以及解释：

> 为什么同一个地图位置，在不同 task state 下会具有不同的 value / optimal action？

---

# 5. Paper 2 — Options

## Citation

Richard S. Sutton, Doina Precup, and Satinder Singh.  
**Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning.**  
Artificial Intelligence, 112(1–2):181–211, 1999.

## BibTeX

```bibtex
@article{sutton1999options,
  title   = {Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning},
  author  = {Sutton, Richard S. and Precup, Doina and Singh, Satinder},
  journal = {Artificial Intelligence},
  volume  = {112},
  number  = {1--2},
  pages   = {181--211},
  year    = {1999},
  doi     = {10.1016/S0004-3702(99)00052-1}
}
```

## 必须讲清楚的问题

Option：

\[
o=\langle I_o,\pi_o,\beta_o\rangle
\]

分别是什么？

- \(I_o\)：initiation set
- \(\pi_o\)：option 内部 policy
- \(\beta_o\)：termination condition

必须理解：

1. primitive action 和 option 的区别；
2. option 为什么使决策过程成为 SMDP；
3. option 执行 \(k\) 步以后，discount 如何处理；
4. SMDP Bellman backup；
5. 什么叫 temporally extended action；
6. option 是“task state transition”还是“实现 task transition 的低层 policy”？这两者必须区分。

## 最小复现

继续使用 Paper 1 的同一张 GridWorld，不重新造环境。

定义三个 options，例如：

```text
go_to_key
go_to_kitchen
go_to_goal
```

每一个 option 有：

```python
initiation(state)
policy(state)
termination(state)
```

实现：

1. primitive-action VI / Q-learning；
2. option-level execution；
3. SMDP Q-learning 或 option-level planning。

## 必须产生的分析

比较：

```text
primitive-only planning
vs.
primitive + options
```

至少报告：

- decision horizon；
- number of high-level decisions；
- convergence / sample efficiency（如果使用 learning）；
- 同一个 option 在不同 task 中是否可复用。

## 和本项目的迁移

把 FSM 上一段：

\[
u_i\rightarrow u_j
\]

和实现它的 low-level navigation option 区分开。

再考虑连续 sequence：

\[
u_i\rightarrow u_j\rightarrow u_k
\]

是否可以被组合为更大的 chunk。

---

# 6. Paper 3 — Policy Sketches

## Citation

Jacob Andreas, Dan Klein, and Sergey Levine.  
**Modular Multitask Reinforcement Learning with Policy Sketches.**  
Proceedings of the 34th International Conference on Machine Learning, PMLR 70:166–175, 2017.

## BibTeX

```bibtex
@inproceedings{andreas2017policy,
  title     = {Modular Multitask Reinforcement Learning with Policy Sketches},
  author    = {Andreas, Jacob and Klein, Dan and Levine, Sergey},
  booktitle = {Proceedings of the 34th International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {70},
  pages     = {166--175},
  year      = {2017},
  publisher = {PMLR}
}
```

## 这篇对我们最重要的思想

一个 task 可以只给出高层 sequence：

```text
get wood -> use workbench
```

另一个 task：

```text
get wood -> use toolshed
```

两个任务共享：

```text
get wood
```

因此可以形成 reusable subpolicy library。

## 必须讲清楚的问题

1. task sketch 是什么？
2. sketch 为什么只规定 abstract subtask sequence，而不规定 primitive implementation？
3. subpolicy 为什么可以跨 task 共享？
4. parameter sharing / modularity 带来的 transfer 是什么？
5. sketch 和 Reward Machine 的差别是什么？
   - sketch 更接近 sequence；
   - Reward Machine 可以表达 branch、loop、interleaving 等更一般的 finite-state structure。
6. sketch 和我们所谓 chunk 的关系是什么？

## 建议的最小复现

**不要求完整复现论文的深度 actor-critic。**

使用离散 GridWorld，构造三个 task：

```text
Task A: get key -> go kitchen
Task B: get key -> go door
Task C: get beef -> go kitchen
```

将每个 abstract subtask 对应一个独立 reusable policy：

```python
subpolicies["get_key"]
subpolicies["go_kitchen"]
subpolicies["go_door"]
subpolicies["get_beef"]
```

要求演示：

- Task A / B 共享 `get_key`
- Task A / C 共享 `go_kitchen`
- 已经学习过的 subpolicy 可以被重新组合到新任务中

### Stretch goal

增加一个 novel task：

```text
get beef -> go door
```

测试 zero-shot / few-shot composition 是否比从头训练更快。

## 验收重点

不是 neural network 细节，而是：

> 能否把“共享的 abstract sequence component”变成明确、可运行的 computational object？

---

# 7. Paper 4 — Hierarchies of Machines (HAM)

## Citation

Ronald Parr and Stuart J. Russell.  
**Reinforcement Learning with Hierarchies of Machines.**  
Advances in Neural Information Processing Systems 10, pp. 1043–1049.

### 年份说明

官方 NeurIPS proceedings 页面将该论文归档为 **NeurIPS 1997**；部分后续论文（包括 Icarte et al. 的参考文献）采用 1998 的会议/出版年份记法。组内 BibTeX 建议统一采用官方 proceedings metadata 的 1997，避免同一文献出现两个 key。

## BibTeX

```bibtex
@inproceedings{parr1997ham,
  title     = {Reinforcement Learning with Hierarchies of Machines},
  author    = {Parr, Ronald and Russell, Stuart J.},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {10},
  pages     = {1043--1049},
  year      = {1997}
}
```

## 必须讲清楚的问题

1. 为什么 hierarchy 可以表示成 machine？
2. machine state 怎样约束当前可选择的 action / submachine？
3. hierarchy 如何缩小 policy search space？
4. 为什么这种约束也可能把全局 optimal policy 排除掉？
5. HAM state 和 Reward Machine state 有什么根本区别？

一个关键区分：

```text
HAM:
machine constrains the policy space

Reward Machine:
machine primarily specifies / exposes reward structure
```

## 建议复现

不要求完整复现原论文实验。

只实现一个极简 hierarchical machine：

```text
Start
  -> NavigateToKey
  -> NavigateToDoor
  -> NavigateToGoal
  -> End
```

然后比较：

```text
unrestricted flat planner
vs.
HAM-constrained planner
```

设计一个小反例，使得 hierarchy 中“局部看起来合理”的约束会排除一条全局更优路径。

目标是理解：

> hierarchy 本身是一种 inductive bias / policy-space restriction。

---

# 8. 四篇论文之间必须能画出的统一关系图

最终 presentation 必须能够画出下面四个 object 的区别。

```text
Environment
    |
    v
Navigation state s
    |
  events
    |
    v
Task FSM / Reward Machine state u
    |
    +------ determines current subtask/reward
    |
    v
Low-level policy / Option
    |
    v
Primitive actions
```

并能够解释：

```text
Reward Machine:
What task stage am I in?

Option:
How do I execute a temporally extended behavior?

Policy Sketch:
How can task-level subtask sequences share reusable modules?

HAM:
How does a finite-state hierarchy constrain the allowed policy space?
```

---

# 9. 代码仓库结构要求

不要把所有内容堆进一个 notebook。

建议一个 repository：

```text
hierarchical_rl_reproduction/
│
├── README.md
├── requirements.txt
│
├── src/
│   ├── envs/
│   │   ├── gridworld.py
│   │   └── officeworld.py
│   │
│   ├── task_fsm/
│   │   ├── labeling.py
│   │   ├── reward_machine.py
│   │   └── task_library.py
│   │
│   ├── algorithms/
│   │   ├── value_iteration.py
│   │   ├── q_learning.py
│   │   ├── qrm.py
│   │   ├── options.py
│   │   └── smdp_q_learning.py
│   │
│   ├── abstractions/
│   │   ├── policy_sketch.py
│   │   └── ham.py
│   │
│   └── visualization/
│       ├── plot_grid.py
│       ├── plot_policy.py
│       └── plot_fsm.py
│
├── notebooks/
│   ├── 01_reward_machine.ipynb
│   ├── 02_options.ipynb
│   ├── 03_policy_sketch.ipynb
│   └── 04_transfer_to_our_task.ipynb
│
├── tests/
│   ├── test_gridworld.py
│   ├── test_reward_machine.py
│   ├── test_product_mdp.py
│   └── test_options.py
│
├── figures/
│
└── notes/
    ├── paper_01_reward_machine.md
    ├── paper_02_options.md
    ├── paper_03_policy_sketch.md
    ├── paper_04_ham.md
    └── transfer_to_project.md
```

---

# 10. Notebook 要求

Notebook 是**讲解和实验入口**，不是主要代码仓库。

每个 notebook 必须包含以下固定结构。

## 10.1 Scientific question

用不超过 5 句话回答：

```text
This paper asks...
The computational problem is...
The representation is...
The proposed algorithm is...
The key prediction/result is...
```

## 10.2 Formal definition

必须自己写出核心数学对象。

禁止只截图论文公式。

## 10.3 Minimal example

使用最小 toy example 手算或打印：

```text
state
event
FSM state
action
next state
next FSM state
reward
```

至少走完整一个 episode。

## 10.4 Implementation

Notebook 中只调用 `src/` 里的模块。

不要在 notebook 里复制几百行 class/function。

## 10.5 Sanity checks

每一个核心对象至少有一个 sanity check。

例如：

```python
assert rm.next_state(u0, {"coffee"}) == u1
```

## 10.6 Main result

必须有一个能够回答 scientific question 的 figure/table。

不能只有：

```text
code runs successfully
```

## 10.7 Interpretation

写三个部分：

```text
What was reproduced?
What was not reproduced?
What did I learn for our project?
```

---

# 11. 代码质量：可靠程序员的最低标准

这是阶段性评估的重要组成部分。

## 11.1 Reproducibility

必须满足：

```bash
git clone ...
pip install -r requirements.txt
pytest
jupyter lab
```

然后 notebook：

```text
Restart Kernel -> Run All
```

可以完整执行。

不能依赖 notebook 之前残留的 hidden state。

## 11.2 不复制作者代码作为主实现

顺序应该是：

1. 先根据论文从头实现 minimal version；
2. 跑通；
3. 再看作者代码；
4. 写一段 comparison：
   - 哪些实现一致？
   - 哪些不同？
   - 为什么？

## 11.3 控制复杂度

原则：

```text
最少依赖
最少 class
最少 abstraction
最小可运行实现
```

不是代码越“工程化”越好。

如果 100 行可以说明问题，不要写成 1000 行 framework。

## 11.4 Core algorithm 必须能解释

以下代码不能出现：

```text
“这是 LLM 写的，我知道能跑，但没有完全看懂。”
```

对于：

- Bellman update
- RM transition
- product-state construction
- option termination
- SMDP backup
- QRM update

必须能够逐行解释。

## 11.5 Test

至少测试：

- environment transition；
- event label；
- RM transition；
- terminal state；
- option termination；
- deterministic toy MDP 的 known optimal value/policy。

## 11.6 Git

建议：

```text
一个明确 feature 一个 commit
```

commit message 例如：

```text
implement reward-machine transition
add product-MDP value iteration
add QRM counterfactual update
add option termination tests
```

避免：

```text
update
fix
final
final2
newnew
```

---

# 12. 每篇论文的讲组会模板

控制在 20–25 分钟。

## Part 1 — Question（3 min）

这篇文章究竟想解决什么问题？

## Part 2 — Representation（5 min）

核心 computational objects 是什么？

## Part 3 — Algorithm（5 min）

输入、输出、update rule。

## Part 4 — Reproduction（7 min）

展示自己的：

- environment
- figure
- learning curve / policy
- sanity checks

## Part 5 — Transfer（5 min）

必须回答：

> 这篇文章中的哪一个 computational object，可以直接迁移到我们的 Navigation × Task-FSM 项目？

---

# 13. 3–4 周执行计划

## Week 1 — Reward Machine

### Deliverables

- `paper_01_reward_machine.md`
- `01_reward_machine.ipynb`
- RM implementation
- product-MDP VI
- 一张不同 \(u\) 下 policy 不同的 figure
- 10–15 分钟内部讲解

### Gate 1

如果不能清楚解释：

\[
S,\; U,\; L,\; \delta_u,\; \delta_r,\; S\times U
\]

不进入下一阶段。

---

## Week 2 — QRM + Options

### 前半周

完成 minimal QRM：

```text
Q-learning vs QRM
```

### 后半周

Options：

```text
I_o
π_o
β_o
SMDP backup
```

### Deliverables

- `qrm.py`
- `options.py`
- `smdp_q_learning.py`
- `02_options.ipynb`
- primitive vs option comparison

### Gate 2

必须能够回答：

> FSM transition 和 option 是不是同一个东西？

正确答案不能只是“差不多”。

---

## Week 3 — Modular composition

重点做 Policy Sketches 的最小离散版本。

### Deliverables

- 3 个 task
- reusable subpolicy dictionary
- 至少两个任务共享同一个 subpolicy
- novel task recombination
- `03_policy_sketch.ipynb`

HAM 这一周以阅读和最小 machine demo 为主，不追完整实验。

---

## Week 4 — 回到我们自己的课题

开始设计：

```text
fixed navigation map
+
multiple task FSMs
```

要求至少构造两种 task structure：

### Condition A

高 subgoal / state modularity

### Condition B

高 repeated-sequence / chunk reuse

并明确区分：

```text
state abstraction pressure
vs.
temporal abstraction pressure
```

### Deliverable

`04_transfer_to_our_task.ipynb`

只做最小 prototype，不追求正式实验。

---

# 14. 70% / 30% 并行安排

## 70%：自己的 reproduction track

这是当前的主任务。

评估：

- 是否按时交付；
- 是否 reproducible；
- 是否理解；
- 是否能够独立 debug；
- 是否能够从 paper 转化为 minimal code；
- 是否能够讲清楚。

## 30%：师兄项目 implementation subtask

周五讨论后确定。

这个任务必须满足：

1. scope 清楚；
2. 输入输出清楚；
3. deadline 清楚；
4. 有已有代码 / mature research question 可以参照；
5. 浩全承担一个完整而可验收的模块。

目的不是“帮忙打杂”，而是观察和学习：

```text
research question
    ↓
model
    ↓
analysis
    ↓
implementation
    ↓
validation
    ↓
figure
```

---

# 15. 阶段性评估标准

建议 3–4 周后从四个维度评估。

## A. Reliability — 40%

- 是否按 deadline 完成；
- 是否需要反复催促；
- 代码是否可运行；
- 是否能独立定位普通 bug；
- 是否能保证已有功能不被新修改破坏。

## B. Conceptual understanding — 30%

能否解释：

- 为什么这么表示；
- 为什么算法这样 update；
- alternative representation 是什么；
- 方法的限制在哪里。

## C. Reproduction quality — 20%

- 是否复现关键 qualitative result；
- sanity checks 是否完整；
- figure 是否能回答问题。

## D. Communication — 10%

- notebook 是否清楚；
- presentation 是否有逻辑；
- 是否能够回答追问。

---

# 16. 阶段结束后的判断

如果能稳定做到：

```text
read
→ formalize
→ implement
→ test
→ reproduce
→ explain
→ transfer
```

下一阶段可以逐渐增加开放式的 task design 和 research question refinement。

如果仍主要表现为：

```text
有明确 specification 时能实现
但难以理解 representation / design logic
```

则后续更适合把工作定位为边界清楚的 computational / implementation module，并继续训练研究设计能力，而不是直接交给高度开放的问题。

---

# 17. Reference BibTeX 汇总

```bibtex
@inproceedings{icarte2018rewardmachines,
  title     = {Using Reward Machines for High-Level Task Specification and Decomposition in Reinforcement Learning},
  author    = {Icarte, Rodrigo Toro and Klassen, Toryn Q. and Valenzano, Richard and McIlraith, Sheila A.},
  booktitle = {Proceedings of the 35th International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {80},
  pages     = {2107--2116},
  year      = {2018},
  publisher = {PMLR}
}

@article{sutton1999options,
  title   = {Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning},
  author  = {Sutton, Richard S. and Precup, Doina and Singh, Satinder},
  journal = {Artificial Intelligence},
  volume  = {112},
  number  = {1--2},
  pages   = {181--211},
  year    = {1999},
  doi     = {10.1016/S0004-3702(99)00052-1}
}

@inproceedings{andreas2017policy,
  title     = {Modular Multitask Reinforcement Learning with Policy Sketches},
  author    = {Andreas, Jacob and Klein, Dan and Levine, Sergey},
  booktitle = {Proceedings of the 34th International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {70},
  pages     = {166--175},
  year      = {2017},
  publisher = {PMLR}
}

@inproceedings{parr1997ham,
  title     = {Reinforcement Learning with Hierarchies of Machines},
  author    = {Parr, Ronald and Russell, Stuart J.},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {10},
  pages     = {1043--1049},
  year      = {1997}
}
```
