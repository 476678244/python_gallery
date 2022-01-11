import numpy as np
import pandas as pd

data = pd.Series(["语文","数学","英语","数学","英语","地理","语文","语文"])
print(data)

# 1、提取不同的值

print(pd.unique(data))

# 2、统计每个值的个数

print(pd.value_counts(data))

# --------------------
df = pd.Series([0,1,1,0] * 2)
print(df)

# dim使用维度表

dim = pd.Series(["语文","数学"])
print(dim)

df1 = dim.take(df)
print(df1)

# -------------

subjects = ["语文","数学","语文","语文"] * 2

N = len(subjects)
df2 = pd.DataFrame({
    "subject":subjects,
    "id": np.arange(N),  # 连续整数
    "score":np.random.randint(3,15,size=N),  # 随机整数
    "height":np.random.uniform(165,180,size=N)  # 正态分布的数据
},
    columns=["id","subject","score","height"])  # 指定列名称的顺序

print(df2)
