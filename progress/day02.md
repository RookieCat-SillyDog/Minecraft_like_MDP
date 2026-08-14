# Day 02

## 今日目标

实现确定性 5×5 GridWorld 环境，包含起点、终点、障碍物和四方向移动。编写至少 5 个测试，明确边界、障碍物与终止状态行为，并检查合法转移。

## 完成情况

完成了 `env/gridworld.py`：

- 起点为 (0, 0)，终点为 (4, 4)。
- 障碍物为 (1, 1)、(2, 2) 和 (3, 1)。
- 非终止状态提供上、下、左、右四个动作。
- 正常移动进入相邻状态；撞到边界或障碍物时保持原位。
- 终止状态没有合法动作，直接请求转移或奖励会抛出 `ValueError`。
- 每个合法动作的即时奖励为 -1.0，折扣因子为 0.9。

地图布局：

```text
=====================
| S | . | . | . | . |
| . | X | . | . | . |
| . | . | X | . | . |
| . | X | . | . | . |
| . | . | . | . | G |
=====================
```

其中 `S` 表示起点，`G` 表示终点，`X` 表示障碍物，`.` 表示可通行位置。

完成了 `tests/test_gridworld.py`，包含 6 个测试：

1. 地图配置和动作。
2. 正常移动。
3. 边界与障碍物碰撞。
4. 终止状态行为。
5. 全部合法状态—动作转移。
6. 奖励、折扣因子和非法输入。

完成了 `docs/gridworld_map.md`，记录地图布局、坐标约定、动作、转移、奖励和验证点。

## 验证结果

从仓库根目录运行：

```powershell
python -m unittest discover -s tests -v
```

实际输出摘要：

```text
test_all_transitions ... ok
test_collision_keeps_position ... ok
test_configuration_and_actions ... ok
test_normal_movement ... ok
test_reward_and_invalid_input ... ok
test_terminal_state ... ok

Ran 6 tests
OK
```

测试结果为 6 项全部通过。全量转移测试遍历了 22 个状态，其中终止状态没有动作；其余 21 个状态共检查 84 个合法状态—动作对。

验证结果：

- 每个合法状态—动作对只有一个转移结果，概率为 1.0。
- 所有下一状态均属于状态空间。
- 边界碰撞和障碍物碰撞均保持原位。
- 终止状态不提供动作，并拒绝转移和奖励请求。
- 起点和终点属于状态空间，3 个障碍物不属于状态空间。

## 遇到的问题

最初的测试脚本依赖手动调用测试函数，并在导入时修改标准输出，导致标准测试发现不稳定和中文输出乱码。现已改为 Python 标准库 `unittest`，使用统一命令自动发现和运行测试。(AI辅助完成)

测试的时候覆盖不到应该检查的很多情况，例如边界碰撞、终止状态行为等。需要AI辅助提示生成案例。

class类的方法、实例化、属性访问、异常处理等 Python 语法细节不熟悉，导致测试脚本中出现了多处错误。

## 下一步

实现迭代式 Policy Evaluation 算法 (`algorithms/policy_evaluation.py`)，在 GridWorld 上评估随机策略，记录 Bellman residual，并生成价值函数的空间分布图。


## 今日知识



### 基础写法

| 知识点 | 用法 | 简单示例 |
| --- | --- | --- |
| `__init__` | 创建对象时自动初始化 | `def __init__(self): self.size = 5` |
| `self` | 表示当前对象，调用时不用手动传入 | `self.env = GridWorld()` |
| 类属性 | 写在类中、方法外，供所有对象共用 | `UP = 0` |
| 类型标注 | 说明变量预期类型 | `start: State = (0, 0)` |
| `@property` | 把方法当属性读取，不加括号 | `states = env.states` |
| `@abstractmethod` | 要求子类实现指定方法 | `def actions(self, state): ...` |
| `_方法名` | 表示类内部使用的辅助方法 | `self._validate_state(state)` |
| 元组解包 | 一次取出多个值 | `probability, next_state = result` |


### `unittest` 常用写法

| 写法 | 作用 |
| --- | --- |
| `class TestGrid(unittest.TestCase)` | 定义测试类 |
| `setUp()` | 每个测试开始前准备环境 |
| `test_...` | 测试方法必须使用此前缀 |
| `assertEqual(a, b)` | 检查两个值相等 |
| `assertTrue(value)` | 检查条件为真 |
| `assertIn(a, values)` | 检查元素属于集合 |
| `assertAlmostEqual(a, b)` | 比较浮点数 |
| `assertRaises(ValueError)` | 检查代码抛出异常 |

最小示例：

```python
class TestGrid(unittest.TestCase):
    def setUp(self):
        self.env = GridWorld()

    def test_start(self):
        self.assertEqual(self.env.initial_state, (0, 0))
```

详细运行测试：

```powershell
python -m unittest discover -s tests -v
```

`-v` 与 `unittest.main(verbosity=2)` 都表示显示详细测试结果。
