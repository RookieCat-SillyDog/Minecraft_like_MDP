# Navigation × Task FSM Demo

这是一个使用 PsychoPy 实现的双空间任务演示：左侧是 Physical / Navigation State Space（物理导航状态空间），右侧是 Abstract Task State Space（抽象任务状态空间）。参与者通过方向键在地图中移动；地图变化产生符号事件，事件驱动右侧 Task FSM（任务有限状态机）转移。

核心流程：

```text
keyboard action
→ GridWorld transition
→ symbolic event detection
→ Task FSM transition
→ display update
→ CSV log
```

## 环境

当前已运行的环境：

- Windows PowerShell
- Python 3.11.16
- PsychoPy 2026.2.3
- PyYAML 6.0.3

从仓库根目录安装：

```powershell
conda create -n week4-demo python=3.11
conda activate week4-demo
python -m pip install -r task_fsm_demo/requirements.txt
```


## 启动

以下命令在仓库根目录运行。

默认启动 Condition A：

```powershell
python -m task_fsm_demo.main
```

指定初始条件：

```powershell
python -m task_fsm_demo.main --condition A
python -m task_fsm_demo.main --condition B
```

指定 participant（参与者）标识：

```powershell
python -m task_fsm_demo.main --condition A --participant sub001
```

查看参数说明：

```powershell
python -m task_fsm_demo.main --help
```

原有的目录内启动方式仍然可用：

```powershell
cd task_fsm_demo
python main.py
```

## 操作

| 按键 | 行为 |
| --- | --- |
| 方向键 | 移动角色 |
| `R` | 重置当前条件并开始新 trial（任务轮次） |
| `1` | 切换到 Condition A，并开始新轮次 |
| `2` | 切换到 Condition B，并开始新轮次 |
| `Esc` | 退出并关闭数据文件 |

按键在按下时处理，不等待松开后再更新画面。任务完成后方向键不再改变状态，但仍可使用 `R`、`1`、`2` 和 `Esc`。

## 地图

两个条件共用仓库根目录 `configs/maps/map_01.yaml` 中的同一张 5×5 地图：

```text
      col 0 1 2 3 4
row 0     . K D . .
row 1     . # . # .
row 2     S # . # G
row 3     . # . # .
row 4     . . B C .
```

- `S`：起点
- `K`：钥匙
- `D`：门
- `B`：牛肉
- `C`：厨房
- `G`：目标
- `#`：占据整个格子的墙，不是转移边上的墙

地图坐标采用 `[row, col]`。没有钥匙时不能进入关闭的门；获得钥匙后进入门格会打开门。进入钥匙、牛肉、厨房或目标格时，事件检测层根据动作前后的环境状态产生符号事件。

## Condition A：Sequential Task

必须按顺序完成：

```text
u0 --GET_KEY--> u1 --OPEN_DOOR--> u2
u2 --GET_BEEF--> u3 --COOK--> u4 --REACH_GOAL--> u5
```


## Condition B：Alternative Routes

可以选择钥匙路线或牛肉路线：

```text
                    GET_KEY       OPEN_DOOR
                 ┌─────────┐    ┌─────────┐
               ↗ │ v1      │ →  │ v2      │ ↘
v0 Start                                         v5 Goal
               ↘ │ v3      │ →  │ v4      │ ↗
                 └─────────┘    └─────────┘
                    GET_BEEF      COOK
```

第一个被 FSM 接受的 `GET_KEY` 或 `GET_BEEF` 决定当前分支。进入一条分支后，另一条分支的事件仍可能由环境产生，但不会推进任务状态。

## 配置坐标的含义

`configs/maps/map_01.yaml` 和 `configs/tasks/` 中任务配置的坐标含义不同：

```text
map_01.yaml 中的 start、walls、objects
→ 实际地图位置 [row, col]
→ GridWorld 使用

task_01.yaml / task_02.yaml 中 states.position
→ FSM 节点的绘图布局坐标 [x, y]
→ 只有 FSMView 使用
```

## 事件规则

当前事件词汇：

```text
GET_KEY
OPEN_DOOR
GET_BEEF
COOK
REACH_GOAL
```

越界、撞墙或无钥匙撞门仍会记录动作，但不产生事件。提前到达目标只产生 `REACH_GOAL`；如果当前 FSM 没有相应转移，任务状态保持不变。

钥匙、牛肉、厨房和目标是可重复进入的事件地点。离开后重新进入可以再次产生相应地点事件。`OPEN_DOOR` 只在门从关闭变为打开时产生一次。

## 数据

程序每次启动都会在 `data/` 中创建新的文件，不覆盖已有结果：

```text
data/sub-<participant>_session-<timestamp>.csv
```

CSV 字段包括：

```text
participant
session
condition
trial
timestamp
step
record_type
trial_status
navigation_state_before
navigation_state_after
fsm_state_before
fsm_state_after
action
event
RT
```

`record_type` 区分 `start`、`action`、`complete`、`reset`、`switch` 和 `exit`。环境状态以 JSON 保存。撞墙动作也会产生一条 `action` 记录。

## 代码结构

```text
src/
├── config.py
├── envs/
│   └── minecraft_grid.py
└── task_fsm/
    ├── fsm.py
    └── labeling.py

configs/
├── maps/map_01.yaml
└── tasks/
    ├── task_01.yaml
    └── task_02.yaml

task_fsm_demo/
├── main.py
├── display/
├── experiment/
├── data/
└── requirements.txt

tests/
├── test_gridworld.py
├── test_event_detector.py
├── test_fsm.py
└── test_routes.py
```



## 测试与验证状态

运行无窗口测试：

```powershell
python -B -m unittest discover -s tests -p "test_*.py"
```
