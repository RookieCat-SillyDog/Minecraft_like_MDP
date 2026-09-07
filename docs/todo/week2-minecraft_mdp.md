# 第二周任务：Minecraft-like MDP

## 1. 第一周结论

第一周任务通过。

已完成统一有限 MDP 接口、GridWorld、Policy Evaluation、Policy Iteration、Value Iteration，以及 PI/VI 的价值一致性检查。现有 24 项自动测试均通过。

第二周的重点不是继续增加动态规划算法，而是检验第一周建立的接口能否直接支持一个同时包含地图状态与元素状态的 Minecraft-like task。

本周暂不实现 Reward Machine、state abstraction、temporal abstraction、options 或 hierarchical RL。

## 2. 开始任务前的思考题

请先独立思考以下问题，并在 `docs/week2_questions.md` 中记录简要答案。答案不要求很长，但需要使用自己的语言，并能够在讨论时脱离文档解释。

1. 请分别写出 Policy Evaluation 和 Value Iteration 的 Bellman 更新。两者在代码中最关键的区别是什么？
2. 为什么第一周的随机策略评估需要 164 轮，而 Value Iteration 只需要 9 轮？
3. 为什么 Policy Iteration 与 Value Iteration 应得到相同的最优价值，却不一定得到完全相同的最优策略？
4. 如果把折扣因子从 $\gamma=0.9$ 改成 $\gamma=0.99$，状态价值、收敛速度和最优路径可能分别发生什么变化？
5. Bellman residual 衡量什么？为什么相邻两轮价值函数的差可以用于判断是否接近 $V^*$？
6. 当前接口使用 `reward(state, action)`。如果即时奖励取决于下一状态，即 $R(s,a,s')$，当前接口是否足够？如果不足，应如何修改？
7. 如果移动一个障碍物，如何在运行程序前预测最优路径长度和起点价值？
8. 在 Minecraft-like task 中，请构造两个位置相同但资源状态不同的例子，说明为什么只用 $(x,y)$ 作为状态不满足 Markov property。
9. 在 `Policy Iteration` 中，为什么策略评估和策略改进需要交替进行？为什么不能只改进一次？
10. 如果 PI 与 VI 的输出不一致，你会按照什么顺序判断是并列最优动作、数值误差、环境错误，还是算法错误？

## 3. 本周总目标

将最小化 Make Bridge 任务定义为有限 MDP：

$$
M=(S,A,T,R,\gamma).
$$

状态至少包含：

$$
s=(x,y,w,i,b),
$$

其中：

- $(x,y)$：agent 的地图位置；
- $w\in\{0,1\}$：是否已经获得 wood；
- $i\in\{0,1\}$：是否已经获得 iron；
- $b\in\{0,1\}$：是否已经制作 bridge。

进入 wood 或 iron 所在位置时自动收集对应资源。wood 与 iron 可以按任意顺序收集。已经获得两种资源后进入 factory，令 $b=1$，任务终止。

默认每个动作奖励为 $-1$，折扣因子为 $\gamma=0.95$。如需采用其他定义，必须在实现前写明理由，并保证文档、代码和测试一致。

## 4. 提交节奏

按照两天一个验收节点执行：

| 节点 | 时间 | 主要内容 | 建议 commit message |
| --- | --- | --- | --- |
| Milestone 1 | Day 6-7 | 补齐第一周复现说明；完成 Minecraft MDP 规格与环境 | `week2-m1: specify and implement minecraft mdp` |
| Milestone 2 | Day 8-9 | 枚举可达状态；复用 PI/VI；完成一致性验证 | `week2-m2: enumerate states and solve minecraft mdp` |
| Milestone 3 | Day 10 | 完成测试、报告、演示和阶段标签 | `week2-m3: complete validation and documentation` |

每个节点至少提交一次有实质内容的 commit。遇到持续超过半个工作日的问题，应当提前记录和汇报，不等到节点结束。

## 5. Milestone 1：规格与环境（Day 6-7）

### 5.1 补齐第一周交付

- [ ] 在 README 中声明经过验证的 Python 版本。
- [ ] 写明创建环境、安装依赖、运行全部测试和运行三个实验的命令。
- [ ] 写明预期测试数量和主要预期输出。
- [ ] 在声明的 Python 版本下，从新环境完成一次安装和运行。
- [ ] 创建 `week1-submission` 标签，并确保它指向第一周接受评估的 commit `3d87b02`，而不是本周新增任务文件的 commit。

### 5.2 完成书面规格

创建 `docs/minecraft_mdp_spec.md`，至少回答：

- [ ] 地图、起点、wood、iron、factory 和障碍物如何定义？
- [ ] 状态空间 $S$ 包含哪些变量？每个变量为什么必要？
- [ ] 动作空间 $A$ 是什么？边界和障碍碰撞如何处理？
- [ ] 转移函数 $T$ 如何更新位置、wood、iron 和 bridge？
- [ ] 奖励 $R$、折扣因子 $\gamma$、初始状态和终止条件是什么？
- [ ] wood 与 iron 为什么必须允许按任意顺序收集？
- [ ] 哪些理论状态不可能从初始状态到达？

### 5.3 实现环境

创建 `env/minecraft.py`。环境必须实现已有 `MDP` 接口。第一周的 `algorithms/` 原则上不得修改；如发现真正的通用接口问题，必须先记录原因，再进行最小修改。

环境测试至少覆盖：

- [ ] 普通移动、边界碰撞和障碍碰撞。
- [ ] 进入 wood 后只更新 wood 状态。
- [ ] 进入 iron 后只更新 iron 状态。
- [ ] wood 和 iron 两种收集顺序都合法。
- [ ] 缺少任一资源时不能制作 bridge。
- [ ] 获得两种资源后进入 factory 可以制作 bridge。
- [ ] bridge 完成后进入终止状态，且终止状态没有动作。
- [ ] 每个合法状态-动作对的转移概率之和为 1。

## 6. Milestone 2：状态图与算法复用（Day 8-9）

### 6.1 枚举状态

从初始状态出发遍历完整转移图，创建 `experiments/enumerate_minecraft_states.py`，输出：

- [ ] 按状态变量直接计算的理论状态数量。
- [ ] 从初始状态实际可达的状态数量。
- [ ] 可达转移数量。
- [ ] 至少三类不可达或不合法状态及其原因。
- [ ] 一张部分状态转移图，清楚显示位置状态和资源状态的共同变化。

不得只根据公式猜测可达状态数；需要通过遍历程序验证。

### 6.2 复用 PI 与 VI

创建 `experiments/run_minecraft.py`，直接调用第一周的 `PolicyIteration` 和 `ValueIteration`：

- [ ] 比较两个算法在全部可达状态上的价值。
- [ ] 报告最大价值差及其对应状态。
- [ ] 输出从初始状态开始的最优路径和资源收集顺序。
- [ ] 检查策略是否能够真正达到终止状态，而不是进入循环。
- [ ] 如果 PI 与 VI 的动作不同，检查两者是否均为并列最优动作。
- [ ] 添加 PI/VI 在 Minecraft 环境上的自动一致性测试。

验收时将检查 `algorithms/` 是否仍然与环境解耦。不得复制出 Minecraft 专用版本的 PI 或 VI。

## 7. Milestone 3：报告与验收（Day 10）

创建 `docs/week2_report.md`，报告不超过 5 页，包含：

- [ ] Minecraft MDP 的完整定义。
- [ ] 理论状态空间与实际可达状态空间的区别。
- [ ] 至少一个 location-only state 违反 Markov property 的例子。
- [ ] PI/VI 的价值一致性结果。
- [ ] 最优路径、资源顺序和结果图。
- [ ] 当前状态中哪些变量更接近 object-level information，哪些变量描述 task progress。
- [ ] 当前模型的限制，以及下一阶段引入任务层状态可能解决的问题。

最终验收包括：

- [ ] 从干净环境按照 README 完成安装、测试和实验运行。
- [ ] 全部自动测试通过。
- [ ] 15 分钟汇报。
- [ ] 不使用 AI，现场修改一个资源位置或折扣因子，先预测结果，再运行程序验证。
- [ ] 能够口头回答第 2 节的思考题。
- [ ] 创建 `week2-submission` 标签，指向最终验收版本。

## 8. AI 工具使用要求

允许使用 AI 辅助学习、排错、测试和绘图，但必须：

- [ ] 在对应进展记录中说明 AI 用于什么问题。
- [ ] 标明哪些代码或测试由 AI 辅助生成。
- [ ] 自己运行并验证 AI 生成的内容。
- [ ] 能够解释和现场修改提交的核心代码。

无法解释、无法修改或没有经过验证的代码，不计为已完成成果。

## 9. 完成判定

本周通过需要同时满足：

- [ ] Minecraft 环境符合书面 MDP 定义。
- [ ] 状态枚举和可达性分析可以重复运行。
- [ ] 第一周的 PI 与 VI 无需环境专用修改即可运行。
- [ ] PI 与 VI 的最优价值在约定数值容差内一致。
- [ ] README 支持从干净环境复现。
- [ ] 思考题和现场修改能够证明对核心概念与代码的理解。

完成本周后，下一阶段再考虑引入 Reward Machine 状态 $u$，将环境状态与任务状态组合为 $S\times U$，并讨论 object level 与 meta level 之间的转换。
