# Navigation × Task-FSM 心理物理实验 Demo
## 开发 TODO 与验收标准

> **目标时间：周五前完成可试玩 Demo**
>
> **实现框架：Python + PsychoPy**
>
> **本周核心目标：先把 representation 做对、代码结构做清楚、Demo 跑稳定。暂时不做 RL learning、复杂度指标或正式心理物理实验分析。**

---

# 1. 本周任务目标

我们当前希望把课题中最核心的 computational structure 做成一个可以直接试玩的心理物理任务：

\[
\text{Navigation Space}
\quad+\quad
\text{Abstract Task / Element FSM}
\]

界面采用左右双 panel：

- **左侧：Navigation / Map Space**
- **右侧：Element / Task State Space**

参与者使用键盘控制 agent 在左侧地图移动。

当 navigation 中出现某个 high-level event，例如：

```text
GET_KEY
OPEN_DOOR
GET_BEEF
COOK
REACH_GOAL
```

右侧 finite-state machine 根据 event 发生 transition，并高亮新的 task state。

本周最重要的事情不是做出一个“完整游戏”，而是验证：

> 人是否能够自然地理解：自己一方面在 physical/navigation state space 中移动，同时也在另一个 abstract task state space 中移动。

---

# 2. 技术选择

第一版使用：

```text
Python + PsychoPy
```

不要使用：

```text
HTML
浏览器版实验
不可修改的自动生成程序
全部依赖 PsychoPy Builder 的自动代码
```

可以直接使用 PsychoPy Python API，例如：

```python
from psychopy import visual, core, event
```

选择 PsychoPy 的主要原因是：

1. 和我们现有的 Python / RL / MDP / FSM 代码在同一生态；
2. 后续可以直接扩展 reaction time、trial、block、condition randomization；
3. 后续如果正式做 psychophysics，可以继续使用同一套程序；
4. 比 Pygame 更适合作为长期实验框架；
5. 不需要为了实验 timing 和数据记录重新造一整套系统。

---

# 3. 第一版 Demo 的界面

## 3.1 左侧：Navigation Space

建议第一版使用：

```text
5 × 5 GridWorld
```

地图中至少包括：

```text
Agent
Key
Door
Beef
Kitchen
Goal
Wall / obstacle
```

参与者使用：

```text
↑ ↓ ← →
```

控制 agent。

暂时不要设计复杂动画、美术素材或者 Minecraft 风格。

图形优先使用 PsychoPy 自带 shape / text：

```text
square
circle
line
text
```

---

## 3.2 右侧：Task / Element State Space

右侧必须画成一个明确的：

```text
Finite State Machine
```

不要只画 inventory bar。

例如：

```text
u0: Start
 |
 | GET_KEY
 v
u1: Key acquired
 |
 | OPEN_DOOR
 v
u2: Door opened
 |
 | GET_BEEF
 v
u3: Beef acquired
 |
 | COOK
 v
u4: Cooked
 |
 | REACH_GOAL
 v
u5: Goal
```

当前 FSM state 必须明显高亮。

---

# 4. 核心 computational structure

必须明确区分：

## Navigation state

\[
s_t \in S_{\mathrm{nav}}
\]

表示 participant 当前在哪里。

## Task state

\[
u_t \in U_{\mathrm{task}}
\]

表示 participant 当前完成任务到了哪一步。

完整状态可以理解成：

\[
(s_t,u_t)
\]

但在界面上必须将两种 state representation 分开画出来。

这是本 Demo 的第一原则。

---

# 5. 程序的数据流

程序中必须存在明确的数据流：

```text
keyboard action
      ↓
Navigation transition
      ↓
event detection
      ↓
Task-FSM transition
      ↓
update display
      ↓
log data
```

建议对应成：

```python
new_nav_state = env.step(action)

events = event_detector.detect(
    previous_state=old_nav_state,
    new_state=new_nav_state
)

new_task_state = task_fsm.step(events)
```

不要让 display 或 experiment controller 直接偷偷修改 task state。

---

# 6. High-Level Event Layer

Navigation environment 和 Task FSM 之间必须有一个显式的 symbolic event layer。

第一版 event vocabulary 建议：

```python
GET_KEY
OPEN_DOOR
GET_BEEF
COOK
REACH_GOAL
```

后续如果需要，可以扩展：

```text
AT_KEY
AT_DOOR
AT_KITCHEN
HAS_KEY
HAS_BEEF
USE_WORKBENCH
```

但第一版保持最小。

---

# 7. 代码结构要求

## 7.1 最重要的要求

**不要把程序写成一个巨大的 `main.py`。**

至少把下面四层分开：

```text
Environment
Task FSM
Display
Experiment Controller
```

推荐 repository：

```text
task_fsm_demo/
│
├── main.py
├── config.py
│
├── environment/
│   ├── gridworld.py
│   ├── objects.py
│   └── event_detector.py
│
├── task/
│   ├── fsm.py
│   └── task_definitions.py
│
├── experiment/
│   ├── controller.py
│   └── logger.py
│
├── display/
│   ├── navigation_view.py
│   ├── fsm_view.py
│   └── hud.py
│
├── configs/
│   ├── map_01.yaml
│   ├── task_01.yaml
│   └── task_02.yaml
│
├── tests/
│   ├── test_gridworld.py
│   ├── test_event_detector.py
│   └── test_fsm.py
│
├── data/
│
└── README.md
```

可以适当简化，但模块责任必须清楚。

---

# 8. Environment 层 TODO

文件：

```text
environment/gridworld.py
```

Environment 只回答：

> 执行 navigation action 之后，地图状态怎么变化？

建议接口：

```python
class GridWorld:
    def reset(self):
        ...

    def step(self, action):
        ...

    @property
    def state(self):
        ...
```

必须支持：

- map boundary；
- wall；
- legal / illegal movement；
- agent position；
- object positions。

Environment **不应该知道当前 FSM state**。

禁止类似：

```python
if at_key:
    task_state = "u1"
```

这种逻辑。

---

# 9. Event Detector TODO

文件：

```text
environment/event_detector.py
```

职责：

> 把 low-level navigation transition 转成 symbolic event。

例如：

```python
def detect_events(prev_state, next_state, world):
    events = set()

    if next_state.position == world.key_position:
        events.add("GET_KEY")

    return events
```

需要测试：

```text
走到 Key -> GET_KEY
走到 Beef -> GET_BEEF
走到 Kitchen 且满足条件 -> COOK
到达 Goal -> REACH_GOAL
```

---

# 10. Task FSM TODO

文件：

```text
task/fsm.py
```

Task FSM 必须是独立的数据结构。

建议：

```python
class TaskFSM:
    def __init__(
        self,
        states,
        initial_state,
        transitions,
        terminal_states
    ):
        ...

    def reset(self):
        ...

    def step(self, events):
        ...

    @property
    def current_state(self):
        ...
```

Transition 推荐数据化：

```python
transitions = {
    ("u0", "GET_KEY"): "u1",
    ("u1", "OPEN_DOOR"): "u2",
    ("u2", "GET_BEEF"): "u3",
    ("u3", "COOK"): "u4",
    ("u4", "REACH_GOAL"): "u5",
}
```

不要用大量：

```python
if ...
elif ...
elif ...
```

把 task rule 写死在 engine 中。

---

# 11. Task Definition TODO

Task definition 必须和 FSM engine 分开。

建议使用：

```text
YAML
```

或者 Python dictionary。

例如：

```yaml
states:
  - u0
  - u1
  - u2
  - u3
  - u4
  - u5

initial_state: u0

terminal_states:
  - u5

transitions:
  - from: u0
    event: GET_KEY
    to: u1

  - from: u1
    event: OPEN_DOOR
    to: u2

  - from: u2
    event: GET_BEEF
    to: u3

  - from: u3
    event: COOK
    to: u4

  - from: u4
    event: REACH_GOAL
    to: u5
```

验收时必须能够：

```text
不修改 Python engine
只换 task config
```

就运行另外一个 Task FSM。

---

# 12. Display TODO

Display 层只负责：

```text
draw
```

不要负责 state transition。

## 12.1 Navigation View

文件：

```text
display/navigation_view.py
```

负责显示：

```text
grid
wall
agent
key
door
beef
kitchen
goal
```

接口建议：

```python
nav_view.draw(env_state)
```

## 12.2 FSM View

文件：

```text
display/fsm_view.py
```

负责：

- draw FSM nodes；
- draw FSM edges；
- draw event labels；
- highlight current state。

建议接口：

```python
fsm_view.draw(
    fsm_definition,
    current_state
)
```

第一版可以手工指定 FSM node coordinates。

暂时不需要实现 automatic graph layout。

---

# 13. Experiment Controller TODO

Controller 负责把各模块串起来。

建议逻辑：

```python
while running:

    nav_view.draw(env.state)
    fsm_view.draw(fsm.definition, fsm.current_state)
    win.flip()

    action, rt = get_response()

    old_nav_state = env.state
    old_fsm_state = fsm.current_state

    new_nav_state = env.step(action)

    events = detector.detect(
        old_nav_state,
        new_nav_state,
        env
    )

    new_fsm_state = fsm.step(events)

    logger.log(...)
```

Controller 可以知道：

```text
env
fsm
display
logger
```

但不要把每个模块的内部规则重新实现一次。

---

# 14. 数据记录 TODO

即使第一版只是 Demo，也必须从第一天开始记录 trial-level / action-level data。

至少保存：

```text
participant
session
condition
trial
timestamp
step
navigation_state_before
navigation_state_after
fsm_state_before
fsm_state_after
action
event
RT
```

建议保存：

```text
CSV
```

例如：

```text
data/sub-001_session-01.csv
```

第一版 participant 可以默认：

```text
demo
```

---

# 15. 周五至少准备两个 Task FSM

两个任务使用：

```text
完全相同的 navigation map
```

只修改：

```text
Task FSM
```

这是本周必须完成的关键 manipulation。

## Condition A：Sequential Task

例如：

```text
Start
 ↓
Get Key
 ↓
Get Beef
 ↓
Cook
 ↓
Goal
```

## Condition B：Branch / Alternative Task

例如：

```text
                 Key route
              ┌──────────────┐
              ↓              │
Start ─────── Key ──────── Goal
  │
  │
  └────────── Beef
                │
              Cook
                │
                ↓
               Goal
```

具体 task logic 第一版可以简单。

关键是验证：

> 同一个 navigation environment 可以加载不同的 abstract task graph。

---

# 16. 周五 Demo 暂时不要实现的内容

本周明确不做：

```text
Q-learning
DQN
QRM
Option learning
Model fitting
Bayesian inference
Formal planning-complexity metric
State-abstraction metric
Temporal-abstraction metric
正式 participant experiment
复杂 trial randomization
```

也不要花大量时间做：

```text
美术素材
动画
声音
Minecraft-like graphics
复杂地图
复杂 crafting rule
```

当前优先级：

\[
\boxed{
\text{representation}
>
\text{software architecture}
>
\text{interaction}
>
\text{appearance}
}
\]

---

# 17. 开发顺序

建议严格按以下顺序完成。

## TODO 1 — GridWorld

完成：

```text
agent movement
walls
objects
reset
```

### Check

可以单独运行一个无 FSM 的 navigation demo。

## TODO 2 — FSM

完成独立 `TaskFSM`。

### Check

不用 PsychoPy，只写一个简单 script：

```python
fsm.step({"GET_KEY"})
fsm.step({"OPEN_DOOR"})
```

输出 state sequence。

## TODO 3 — Event Detector

完成 navigation → symbolic event。

### Check

自动测试：

```text
agent 到 Key -> GET_KEY
agent 不在 Key -> 不产生 GET_KEY
```

## TODO 4 — Navigation View

把地图画到 PsychoPy 左 panel。

## TODO 5 — FSM View

把 FSM 画到 PsychoPy 右 panel。

## TODO 6 — Controller

将：

```text
keyboard
env
event
fsm
display
```

串起来。

## TODO 7 — Logger

每一步输出 CSV。

## TODO 8 — 第二个 Task FSM

确保：

```text
same map
different FSM
```

无需修改核心代码。

## TODO 9 — README

写清楚：

```bash
pip install -r requirements.txt
python main.py
```

以及按键说明。

## TODO 10 — Clean-machine test

正式交付前：

```text
关闭程序
重新启动 Python 环境
重新运行
```

确认不存在依赖 notebook hidden state 或本地特殊路径的问题。

---

# 18. 周五现场试玩流程

建议现场只做 10–15 分钟。

## Step 1

展示代码结构，不超过 2 分钟。

回答：

> Environment、FSM、event detector、display 分别在哪里？

## Step 2

大家试玩 Condition A。

观察：

- 是否理解左、右两个空间；
- 是否知道为什么 FSM state 改变；
- UI 是否有歧义；
- input 是否流畅。

## Step 3

不改变地图，切换 Condition B。

观察：

> 仅仅改变 FSM，participant 的 planning 感受是否已经改变？

## Step 4

讨论下一步 task design，而不是现场继续调代码。

---

# 19. 验收标准

这次验收分成两个层面：

1. **Demo 是否成功表达 scientific representation**
2. **是否证明自己是一个可靠的程序员和实施者**

---

# 20. A. Functional Correctness — 30%

必须全部通过。

### A1. Navigation

- [ ] agent 可以稳定移动；
- [ ] 不能穿墙；
- [ ] 不会走出地图；
- [ ] reset 正常。

### A2. Event

- [ ] Key event 正确；
- [ ] Door event 正确；
- [ ] Beef event 正确；
- [ ] Kitchen / Cook event 正确；
- [ ] Goal event 正确。

### A3. FSM

- [ ] 初始 state 正确；
- [ ] 合法 event 导致正确 transition；
- [ ] 非法 event 不应错误改变 FSM；
- [ ] terminal state 工作正常。

### A4. Synchronization

试玩过程中必须保证：

```text
左侧发生 event
        ↓
右侧 FSM 同步变化
```

不存在状态不同步。

---

# 21. B. Representation Quality — 20%

这是科学层面的验收。

周五必须能够清楚回答：

### B1.

左边的 state 和右边的 state 分别是什么？

正确回答应接近：

\[
s_t \in S_{\mathrm{nav}}
\]

和

\[
u_t \in U_{\mathrm{task}}
\]

### B2.

为什么不直接把 Key / Beef / task progress 全部塞进 GridWorld state？

需要能够解释：

> 我们希望显式区分 environment/navigation structure 和 abstract task structure。

### B3.

event layer 的作用是什么？

需要解释：

> event 将 low-level physical state transition 映射成 task-level symbolic transition。

### B4.

为什么固定地图、改变 FSM 对我们后续实验重要？

需要解释：

> 这样可以减少 navigation topology 变化造成的混淆，把 manipulation 更集中到 task representation structure。

---

# 22. C. Software Architecture — 20%

检查代码，而不是只看 Demo。

### 必须满足

- [ ] Environment 不直接修改 FSM；
- [ ] FSM 不负责 drawing；
- [ ] Display 不修改 environment；
- [ ] event detector 是独立层；
- [ ] Task definition 和 FSM engine 分离；
- [ ] Map definition 和 rendering code 尽量分离；
- [ ] 第二个 task 不需要复制一份完整程序。

### 明显不合格的情况

例如：

```text
main.py 1000+ lines
```

并且大量出现：

```python
if key:
    draw...
    task_state...
    reward...
    agent...
```

混在一起。

或者为了增加 Condition B：

```text
复制整个 task_A.py
改成 task_B.py
```

这不算完成模块化要求。

---

# 23. D. Reproducibility & Reliability — 20%

这是“可靠实施者”的核心检查。

必须满足：

### D1. 一键启动

README 中明确：

```bash
python main.py
```

即可运行。

### D2. Environment independence

不能依赖：

```text
个人电脑绝对路径
手动复制素材
IDE 特殊配置
上一次运行残留变量
```

### D3. Data

每次运行都产生结构清楚的数据文件。

### D4. Crash

正常试玩过程中不应：

```text
随机 crash
卡死
按键失效
状态跳错
```

### D5. Deadline

周五见面前必须提交一个：

```text
能运行的版本
```

而不是：

```text
大部分写完了，但还有一个 bug，所以暂时跑不了。
```

对于这次任务：

> **稳定的简单版本 > 功能很多但无法稳定运行的版本。**

---

# 24. E. Code Understanding — 10%

现场随机选择几个核心函数，要求解释：

```text
GridWorld.step()
detect_events()
TaskFSM.step()
controller loop
logger.log()
```

至少能够说明：

```text
input
output
state change
为什么这样设计
```

不能出现：

> “这段主要是 LLM 帮我写的，我知道能跑，但是具体细节还没有完全看。”

可以使用 LLM 辅助，但提交者必须对最终代码负责。

---

# 25. 总评分

| 维度 | 权重 |
|---|---:|
| Functional correctness | 30% |
| Representation quality | 20% |
| Software architecture | 20% |
| Reproducibility & reliability | 20% |
| Code understanding | 10% |
| **Total** | **100%** |

建议：

```text
≥ 85%：通过，可以进入下一阶段
70–84%：基本通过，需要修正后再进入
< 70%：先继续 implementation / reproduction training
```

其中以下属于 **hard gate**：

1. Demo 必须能稳定运行；
2. 左右两个 state space 必须真正独立实现；
3. 必须有 event layer；
4. 至少两个 FSM 可以使用同一张地图切换；
5. 核心代码本人能够解释。

任何一个 hard gate 没有满足，都暂时不进入复杂 task design。

---

# 26. 我们周五真正要检验的问题

周五不是要检验：

> “这个实验已经能不能发 paper？”

而是检验下面四件事。

## 1. Representation

这个双空间 representation 是否清楚、自然？

## 2. Interaction

人玩的时候能不能理解：

```text
physical movement
vs.
abstract task progress
```

## 3. Extensibility

以后更换：

```text
FSM topology
task sequence
branch
loop
chunk
subgoal
```

是否不需要重写整个程序？

## 4. Reliability

给定一个明确 specification，是否能够：

```text
理解
→ 分解
→ 实现
→ 测试
→ 交付
→ 解释
```

这也是当前阶段对浩全最重要的训练目标之一。

---

# 27. 周五之后可能进入的第二阶段

如果这一版通过验收，再讨论第二阶段：

## A. Equal-cost dual route

构造：

```text
Key + Door + Shortcut
```

与：

```text
Direct long navigation route
```

满足：

\[
C_{\text{key+shortcut}}
\approx
C_{\text{direct navigation}}
\]

## B. Training / Transfer

研究过去形成的 task representation 如何影响新任务搜索。

## C. State abstraction manipulation

改变 task-FSM topology 中：

```text
bottleneck
gateway
module
```

结构。

## D. Temporal abstraction manipulation

改变：

```text
repeated transition sequence
reusable chunk
```

的统计结构。

但是这些都不是本周任务。

---

# 28. 本周一句话标准

> **周五前做出一个结构清楚、稳定可运行、可切换两个 Task FSM、左右状态同步、数据可记录、本人能完整解释的 PsychoPy Demo。**

本周不追求复杂。

先把最小系统做对。
