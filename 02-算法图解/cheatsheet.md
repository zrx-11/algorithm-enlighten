# 速查表

## 大O运行时间速查（从快到慢）

| 大O | 名称 | n=1024 时操作数 | 代表算法 |
|---|---|---|---|
| O(1) | 常量时间 | 1 | 散列表查找、读数组第 k 个 |
| O(log n) | 对数时间 | 10 | 二分查找 |
| O(n) | 线性时间 | 1024 | 简单查找、打印每个元素 |
| O(n log n) | —— | ~10000 | 快速排序（平均）、合并排序 |
| O(n²) | 平方时间 | ~100万 | 选择排序、乘法表 |
| O(2ⁿ) | 指数时间 | 天文 | 集合覆盖精确解 |
| O(n!) | 阶乘时间 | 天文 | 旅行商蛮力解 |

## 数据结构操作速查

| 操作 | 数组 | 链表 | 散列表（平均） |
|---|---|---|---|
| 随机读取 | O(1) | O(n) | —— |
| 顺序读取全部 | O(n) | O(n) | —— |
| 插入 | O(n) | O(1) | O(1) |
| 删除（已定位） | O(n) | O(1) | O(1) |
| 按键查找 | —— | —— | O(1) |

## 算法选择速查

| 问题类型 | 首选算法 | 运行时间 |
|---|---|---|
| 有序列表查元素 | 二分查找 | O(log n) |
| 无序查找 | 简单查找 | O(n) |
| 通用排序 | 快速排序 | 平均 O(n log n) |
| "键→值"映射/查重/缓存 | 散列表 | O(1) |
| 图里段数最少路径 | BFS | O(V+E) |
| 加权图最短路径（正权） | 狄克斯特拉 | O(V²) 量级 |
| 含负权边最短路径 | 贝尔曼-福德 | —— |
| NP 完全问题 | 贪婪近似 | O(n log n) ~ O(n²) |
| 约束下求最优、子问题独立 | 动态规划 | O(网格大小) |
| 新样本分类/数值预测 | KNN | 找最近 K 个 |

## Python 代码片段速查

```python
# 二分查找
def binary_search(list, item):
    low, high = 0, len(list)-1
    while low <= high:
        mid = (low + high) // 2
        if list[mid] == item: return mid
        if list[mid] > item: high = mid - 1
        else: low = mid + 1
    return None

# 快速排序
def quicksort(array):
    if len(array) < 2: return array
    pivot = array[0]
    less = [i for i in array[1:] if i <= pivot]
    greater = [i for i in array[1:] if i > pivot]
    return quicksort(less) + [pivot] + quicksort(greater)

# BFS（图用 dict 表示）
from collections import deque
def search(name):
    queue = deque(graph[name]); searched = []
    while queue:
        person = queue.popleft()
        if person not in searched:
            if person_is_seller(person): return True
            queue += graph[person]; searched.append(person)
    return False
```

## 关键数字记忆点

- 128 个元素二分查找最多 **7** 步；翻倍到 256 → **8** 步。
- 40 亿元素 → 二分查找约 **32** 步；简单查找 = **40 亿步 ≈ 11 天**。
- 散列表填装因子 **> 0.7** 就扩容。
- 5 个城市旅行商 = **120** 条路线；6 城 = 720；7 城 = 5040。
- KNN 邻居数经验值：**√N**。
