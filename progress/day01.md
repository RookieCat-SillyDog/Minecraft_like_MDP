# Day 01

## 今日目标

阅读 *Algorithms for Decision Making* 第 7 章相关内容，明确有限 MDP 的基本定义，并建立后续环境和动态规划算法共用的 MDP 接口。

## 完成情况

完成了 `docs/mdp_definition.md`，说明了 $S$、$A$、$T$、$R$、$\gamma$、策略和价值函数的含义，以及这些定义与代码接口的对应关系。

完成了 `env/mdp.py`，定义了所有环境共用的抽象接口：

- `states`
- `initial_state`
- `discount_factor`
- `actions(state)`
- `transitions(state, action)`
- `reward(state, action)`
- `is_terminal(state)`



## 验证结果

使用一个仅包含初始状态和终止状态的最小 MDP 示例检查接口。该示例只在终端中运行，没有保存为测试文件。

- 预期 `env/mdp.py` 能通过 Python 语法检查；实际检查通过。
- 预期 `MDP` 不能被直接实例化；实际创建实例时正确抛出 `TypeError`。（AI补充完成）
- 预期具体环境必须实现全部七项接口；临时两状态 MDP 实现后能够正常实例化和调用。（AI补充完成）
- 预期合法动作的转移概率之和为 1；实际结果为 1.0。


## 遇到的问题

最初考虑在每个转移结果中保存奖励，后来根据教材统一改为 $R(s,a)$，由 `reward(state, action)` 单独返回期望即时奖励。



## 下一步

实现确定性的 $5\times5$ GridWorld，明确起点、终点、障碍、边界和终止状态行为，绘制地图，并为环境编写至少 5 个测试。
