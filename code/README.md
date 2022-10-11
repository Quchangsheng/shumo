# 代码使用及主要框架

主要依赖包：

* python3.7

* 数据类：pandas, numpy
* 工具类：tensorboard, pytorch, opencv-python, matplotlib

## 代码框架

* 可以选择先用贝叶斯优化选择上述价值更新的超参数，运行bayesian_opt.py文件。代码中已经以常数形式给出了我们通过贝叶斯优化选取的参数，因此可以直接运行;

* 问题一和问题二分为两个执行文件，分别为`main.py`和`main_q2.py`，其中分别包含相应所需函数模块;

## 代码使用

### 问题一：

***注：说明部分以A1为例***

* **执行文件**：main.py

* **参数调整**：对数据集A1进行处理时，调整util.py文件第14、15、16行参数

```python
num = 1   # 对应要处理的data集合，调整为相应数字
word = 'A'   # 对应问题1
max_step = 1000   # 训练item价值的迭代次数
```

其中问题1的迭代次数推荐区间[500, 1000]，大约执行时间在[0.8, 2]h，依据数据量不同而变化。

* **主要模块**：

```python
def train(items, train_max_step, params):
```

每次迭代都产生一次排样方案，因此可以不等到迭代完成随时停止，用于迭代item价值评估部分。

* **输出说明**：

<u>打印信息</u>和<u>保存文件</u>均在上述train函数中，函数中每部分功能都有注释

**打印信息**：

1. 包含每次迭代排样过程开始和结束的信息；
2. 排样完成的利用率。

**文件保存**：

1. 在log文件夹生成迭代过程利用率的变化，命名方式为 “日期-小时-分钟”，在terminal输入以下代码，并打开网址，可以看到实时利用率变化曲线；

```python
tensorboard --logdir=log
```

2. 在`./result`文件夹的相应 ’数据集A1‘ 中产生所有step的文件夹，命名方式为'step+利用率'，文件夹中包括排样方案 ‘data.csv’ 文件。最后提交的排样方案重命名为 'cut_program.csv' 。

### 问题二：

***注：说明部分以B1为例***

* **执行文件**：main_q2.py

* **参数调整**：对数据集B1进行处理时，调整util.py文件第14、15、16行参数

```python
num = 1   # 对应要处理的data集合，调整为相应数字
word = 'B'   # 对应问题2
max_step = 50   # 训练item价值的迭代次数
```

其中问题2的迭代次数推荐区间[10, 50]，大约执行时间在[0.3, 1.5]h，依据数据量不同而变化。

* **主要模块**：

```python
def calculate_dist_for_batches(batches, material_list):
```

计算batch之间的相似程度，用于判断是否希望把两个batch合并，输出为 ‘距离矩阵’ ，描述两个batch的相似程度；

```python
def make_cluster(batches, dist_matrix):
```

依据上述 ‘距离矩阵’ 对batches进行聚类操作，在主函数中循环调用以上两个模块，直到再没有batch发生变化，则跳出循环；

```python
# 保存当前聚类结果
def store_batches(batches):
# 读取当前聚类结果
def read_batches(orders):
```

以上两个模块功能由注释所示，用于保存和读取聚类结果，主要用于节省时间，避免每次运行都需要重新聚类。聚类结果保存在相应`./result/数据集B1/batch.csv`文件中。主函数中若该文件存在，则直接读取聚类结果，否则初始化batches并重新聚类；

```python
def check_clusters(batches, orders):
```

检查聚类结果是否满足题目要求，同时确保订单没有重复，没有漏用；

```python
def train(items, train_max_step, params):
```

聚类出一个组批方式后按照问题一的解决方式，区分材料地调用train模块，由于材料种类繁多，且数据集本身数据量远大于dataA，因此推荐迭代次数max_step <= 50。

* **输出说明**：

<u>打印信息</u>和<u>保存文件</u>均在main函数中，函数中每部分功能都有注释

**打印信息**：

1. 包含聚类和排样过程的相关信息，其中包含对聚类结果的检查；
2. 排样完成的各个batch的利用率以及数据集B1的整体利用率。

**文件保存**：

1. 在`./result`文件夹的相应 ’数据集B1‘ 中产生聚类结果 ‘batch.csv’ 文件，避免每次运行代码重新聚类耗费时间，若需要重新聚类删除该文件即可；
2. 保存排样方式在`./result/数据集B1/data_().csv`，括号内容为该数据集合的整体材料利用率。提交时重命名为 ‘sum_order.csv’。

