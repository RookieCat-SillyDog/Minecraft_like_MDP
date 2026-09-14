# 当前三因子 Factored MDP 设定

> 本文档记录 `env/factored_minecraft/` 当前实际实现的 MDP 设定，与 `docs/week3_factored_abstraction.md` 任务书的差异均为有意化简。数值全部来自 `python -B -m analysis.analyze_factored_tasks` 的真实输出，代码位置均给出相对路径。

## 1. 与任务书的有意偏离

| 项目 | 任务书 | 当前实现 |
| --- | --- | --- |
| Key factor | $k=(k_h,k_t)$，$3\times3=9$ 状态 | 一维颜色等级，3 状态 |
| Beef factor | $b=(b_c,b_d)$，$3\times3=9$ 状态 | 一维烹饪等级，3 状态 |
| Beef 动作 | `cook` 和 `cut` 两个动作模式 | 只有 `cook`，没有 `cut` 和 cutting board |
| 理论联合空间 | $9^3=729$ | $3\times3\times3=81$ |
| 可达状态数 | 729 的可达子集 | 81 或 63（见第 6 节） |
| 钥匙门数量 | 门两侧都能不靠钥匙到达，2 个有向耦合模板 | 门是目标区域的唯一通道，1 个有向耦合模板（原因见第 6 节） |
| 展示信息 | 绘图坐标和语义标签在 task configuration 中 | 移入 `analysis/plot_factored_tasks.py`，环境不依赖展示 |

化简后保留的核心结构不变：三因子联合状态、每个动作只改变一个 factor、真正的 BFS 可达枚举、schema/template 两级耦合计数、四个 anchors。

## 2. 三个 factor

联合状态为 $x=(l,k,b)$，类型定义见 `env/factored_minecraft/maps.py`：

```python
JointState = tuple[GridState, str, str]   # (location, key, beef)
```

| Factor | 下标 | 状态数 | 状态 | 动作 | 内部边 |
| --- | ---: | ---: | --- | --- | ---: |
| Location $l$ | `location = 0` | 9 | $(row, col)$，$row,col\in\{0,1,2\}$ | `up` / `down` / `left` / `right` | 20 条有向边 |
| Key $k$ | `key = 1` | 3 | `blank` → `shallow blue` → `blue` | `dye` | 2 条有向边 |
| Beef $b$ | `beef = 2` | 3 | `raw` → `medium` → `well` | `cook` | 2 条有向边 |

理论联合空间为 $3\times3\times3=81$；`env.states` 只包含 BFS 可达子集。

### 2.1 Location 图

- $3\times3$ 网格，四方向移动，越界和墙都直接不进入 `factor_moves`，不产生失败 self-loop。
- 两面墙：$(0,1)$–$(0,2)$ 和 $(2,1)$–$(2,2)$（`maps.py` 的 `_walls`）。
- 一扇门：$(1,1)$–$(1,2)$（`_door_edge`），由 `blue_key_opens_door` 规则控制。
- 地标：`start=(2,0)`、`goal=(2,2)`、`kitchen=(1,1)`。

### 2.2 Key 图

`blank --dye--> shallow blue --dye--> blue`。`dye` 不依赖任何其他 factor。

### 2.3 Beef 图

`raw --cook--> medium --cook--> well`。`cook` 是否可用由 location 规则控制。

## 3. 动作与 MDP 接口

实现见 `env/factored_minecraft/environment.py`。

- 动作域按 `action_spec` 固定顺序排列：`up/down/left/right`（location）、`dye`（key）、`cook`（beef）。每个动作通过 `ACTION_FACTOR`（`dict(action_spec)`）映射到唯一 factor，只改变该 factor。
- 不可执行动作不出现在 `actions(state)` 中；不合法转移直接不存在，不是失败 self-loop。
- 转移是确定性的：`transitions(state, action) = [(1.0, next_state)]`。
- 每个非终止动作奖励 $-1$；折扣因子 $\gamma=0.95$。
- 终止状态是 `goal_state = ((2,2), "blue", "well")`；终止状态没有合法动作，价值为 0。
- `states` 由 initial state 出发沿真实 `successors()` 做 BFS 得到，同时建立后继缓存 `_successors`。断连的 joint 状态不会被声明。
- `successors(map_config, state, rules)` 是唯一的 gate 语义实现：动作先查 `factor_moves`，再依次过每条规则，任一规则返回 `False` 即排除该后继。

规则签名是普通函数：

```python
allowed = rule(map_config, state, edge)
```

其中 `edge = (source_factor_state, action, target_factor_state)` 是受控 factor 上的局部边。

## 4. 耦合规则与四个 anchors

实现见 `env/factored_minecraft/tasks.py`。当前只有两条耦合规则，其余四个方向的耦合为 0：

| 规则 | 方向 | 语义 |
| --- | --- | --- |
| `blue_key_opens_door` | $K\to L$ | 门边 $(1,1)$–$(1,2)$ 只在 `state[key] == "blue"` 时开放 |
| `cook_only_in_kitchen` | $L\to B$ | `cook` 只在 `state[location] == kitchen` 即 $(1,1)$ 时可用 |

```python
task_rules = {
    "independent": (),
    "key_gates_location": (blue_key_opens_door,),
    "location_gates_beef": (cook_only_in_kitchen,),
    "combined": (blue_key_opens_door, cook_only_in_kitchen),
}
```

任务语义（颜色名、食物名、地标名）全部通过 `maps.py` 和 `tasks.py` 的数据/规则给出，`environment.py` 不含任何具体任务语义。

## 5. 耦合复杂度指标

实现见 `analysis/coupling.py` 和 `analysis/shortest_paths.py`，全部从 BFS 得到的 reachable joint graph 计算。

- **Schema count $S_{i\to j}$**：按动作名聚合的耦合规则数。同一动作名的所有模板，只要有任一 context 使结果不同，就记 1 个 schema。
- **Template count $K_{i\to j}$**：按局部边 $(source, action, target)$ 聚合。该边在不同 conditioning factor 取值下结果不同，才算耦合模板。
- **Instance count $M_{i\to j}$**：耦合模板在可达状态中的实际出现次数（分母为全部模板实例）。
- **Template proportion / instance proportion**：分别以模板数和实例数为分母。
- **$L^*$**：初始状态到最近终止状态的最短路径长度，由 `shortest_path_dag()` 的 BFS 得到。
- **$N_{K\to L}$、$N_{L\to B}$ range**：最短路径 DAG 上每条路径经过的耦合边数的最小/最大值。
- **$D$（switch）range**：路径上相邻动作所属 factor 发生切换次数的最小/最大值。

范围在 shortest-path DAG 上动态传播计算，不枚举全部路径，也不依赖 PI/VI 的 tie-breaking。

## 6. 四个 anchors 的当前数值

全部锚点 $L^*=8$，PI 与 VI 价值最大差为 0：

| anchor | $S_{K\to L}$ | $S_{L\to B}$ | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $N_{K\to L}$ range | $N_{L\to B}$ range | $D$ range | reachable states | shortest paths |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| independent | 0 | 0 | 0 | 0 | 8 | [0, 0] | [0, 0] | [2, 7] | 81 | 840 |
| key_gates_location | 1 | 0 | 1 | 0 | 8 | [1, 1] | [0, 0] | [2, 7] | 63 | 336 |
| location_gates_beef | 0 | 1 | 0 | 2 | 8 | [0, 0] | [2, 2] | [3, 6] | 81 | 56 |
| combined | 1 | 1 | 1 | 2 | 8 | [1, 1] | [2, 2] | [3, 6] | 63 | 30 |

要点：

- `key_gates_location` 的门把部分 $(l,k,b)$ 与 initial 隔断，可达状态从 81 降到 63（被隔断的 18 个状态是 $l\in\{(0,2),(1,2),(2,2)\}$ 且 key 不是 `blue` 的组合）。
- `location_gates_beef` 不影响可达性（kitchen 本来就在可达区域内），仍是 81，但 `cook` 只剩 kitchen 中 2 个实例，即 $K_{L\to B}=2$、$M_{L\to B}=2$。
- $S_{L\to B}=1$ 而 $K_{L\to B}=2$：两个 `cook` 模板（`raw→medium` 和 `medium→well`）共享同一个动作名 schema。
- $S_{K\to L}=1$、$K_{K\to L}=1$ 的原因不是 key 降维，也不是门只挡一个方向（门在两个方向上都挡移动），而是**门的位置**：墙 $(0,1)$–$(0,2)$ 和 $(2,1)$–$(2,2)$ 把目标区域 $\{(0,2),(1,2),(2,2)\}$ 与其余部分隔开，门是唯一通道。所以 key 不是 `blue` 时永远到不了 $(1,2)$，可达状态中 $l=(1,2)$ 的状态全都是 `blue` key，反向边 $(1,2)\to(1,1)$ 在可达 context 中不出现结果差异，不构成耦合模板。耦合模板计数只看可达 context 中是否存在结果差异，不看规则在完整图上是否双向生效。若把门移到两侧都能不靠钥匙到达的位置（如 $(0,1)$–$(1,1)$），同样的一维 key 和同一条规则会得到 $S_{K\to L}=2$、$K_{K\to L}=2$，与任务书一致。任务书中的 (2,2) 隐含了这种两侧可达的门位置设定。
- 最短路径数量差异很大（840 到 30），说明 anchors 之间仍存在 nuisance differences，比较耦合复杂度时须结合 $L^*$ 与路径数一起读。

动作可用性（全部非终止可达状态平均）：

| anchor | 非终止状态 | 总可用动作 | mean(L/K/B) | 平均分支因子 |
| --- | ---: | ---: | --- | ---: |
| independent | 80 | 287 | 2.237/0.675/0.675 | 3.587 |
| key_gates_location | 62 | 221 | 2.306/0.581/0.677 | 3.565 |
| location_gates_beef | 80 | 239 | 2.237/0.675/0.075 | 2.987 |
| combined | 62 | 185 | 2.306/0.581/0.097 | 2.984 |

## 7. 代码位置速查

| 需求 | 文件 |
| --- | --- |
| 改地图、墙、门、厨房、地标、initial/goal | `env/factored_minecraft/maps.py` |
| 改 factor 状态或局部转移 | `env/factored_minecraft/maps.py` |
| 改耦合条件或 anchors 组合 | `env/factored_minecraft/tasks.py` |
| 改执行逻辑（BFS、接口） | `env/factored_minecraft/environment.py` |
| 改耦合指标 | `analysis/coupling.py` |
| 改最短路径指标 | `analysis/shortest_paths.py` |
| 改汇总与打印 | `analysis/analyze_factored_tasks.py` |
| 改图形与展示标签 | `analysis/plot_factored_tasks.py` |

## 8. 运行命令

```bash
python -m analysis.analyze_factored_tasks   # 四个 anchors 的耦合、路径与 PI/VI 对比
python -m unittest discover -s tests -v     # 全部测试
python -m analysis.plot_factored_tasks      # 覆盖 figures/ 中的图片
```
