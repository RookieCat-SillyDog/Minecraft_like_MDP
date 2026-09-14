# Day 16

## 目标

按 `REFACTOR_PLAN_env.md` 简化 `env/factored_tasks.py` 与 `env/factored_minecraft.py`，删除 shallow 抽象，同时保持四个 factored task anchors 的数值行为不变。

## 完成情况

- 先修复 Key 图构造中的破坏性改动：`source = (tail)` 已恢复为 `source = (head, tail)`，重构前基线测试通过。
- 删除 `FactorGraph`、`DirectedTransition`、`AvailabilityRule`、`ExactTerminalPredicate`、`FactoredTaskConfig.validate()` 及相关运行时校验链。
- 三张因子图改为三个 move dict：`LOCATION_MOVES`、`KEY_MOVES`、`BEEF_MOVES`。
- 因子标识改为联合状态下标：`LOCATION=0`、`KEY=1`、`BEEF=2`，动作到因子的关系由 `ACTION_FACTOR` 表示。
- 门控规则统一为 `Gate`，方向由 `Gate.condition` 和受控 edge 所属动作因子共同决定。
- `FactoredMinecraftMDP` 改为一次 BFS 同时建立可达状态和动作后继表，保留性能必需的查找表。
- 新增 `successors(task, state)` 作为唯一的 gate 语义实现，`plot_factored_tasks.py` 的重复后继逻辑已删除。
- 展示标签、坐标和地标移入 `experiments/factored_display.py`，`env/` 只保留动力学。

## 与旧 spec 的有意偏离

- 绘图坐标和语义标签不再放在 task 配置中，而是放在 `experiments/factored_display.py`。环境不依赖展示信息，减少了动力学层和展示层的耦合。
- 删除 `_validate_state` 和 `_validate_action`。PI/VI 只遍历 `env.states`，正常路径行为不变；错误路径现在来自 dict 查找，异常类型为 `KeyError`。
- 删除 `primitive_costs` 和 `query_set`。当前所有原语代价均为 `1.0`，查询起点只有 `initial_state` 一个，预留字段没有实际行为。

## 验证

实际运行：

```text
python -B -m experiments.analyze_factored_tasks
python -B -m unittest discover -s tests
python -B -m experiments.plot_factored_tasks
python -B MDP/show_factored_mdp.py
```

结果：

- `analyze_factored_tasks` 与重构前基线逐行一致。
- 完整测试 67 项通过。
- 绘图脚本生成五组 PNG 和 SVG，没有字体 warning。
- demo 脚本成功展示三张因子图，并执行 10 步路径到达终止状态。
