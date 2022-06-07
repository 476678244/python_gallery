# https://juejin.cn/post/7051548941931806728
# 交换变量
a = 3
b = 6
a, b = b, a
print(a)
# >>>6
print(b)
# >>>3

# 字典推导(Dictionary comprehensions)和集合推导(Set comprehensions)
some_list = [1, 2, 3, 4, 5]
another_list = [x + 1 for x in some_list]
print(another_list)

some_list = [1, 2, 3, 4, 5, 2, 5, 1, 4, 8]
even_set = {x for x in some_list if x % 2 == 0}
print(even_set)
d = {x: x % 2 == 0 for x in range(1, 11)}
print(d)

my_set = {1, 2, 1, 2, 3, 4}
print(my_set)

# 计数时使用Counter计数对象

from collections import Counter

c = Counter('helloworld')
print(c)
print(c.most_common(2))

# 漂亮的打印出JSON
import json

data = {"status": "OK", "count": 2, "results": [{"age": 27, "name": "Oz", "lactose_intolerant": "true"},
                                                {"age": 29, "name": "Joe", "lactose_intolerant": "false"}]}
print(json.dumps(data))  # No indention
print(json.dumps(data, indent=2))

#  连接
nfc = ["Packers", "49ers"]
afc = ["Ravens", "Patriots"]
print(nfc + afc)
print(str(1) + " world")
print('1' + " world")
print(1, "world")
print(nfc, 1)

# 数值比较
x = 2
if 3 > x > 1:
    print(x)
if 1 < x > 0:
    print(x)

# 同时迭代两个列表
nfc = ["Packers", "49ers"]
afc = ["Ravens", "Patriots"]
for teama, teamb in zip(nfc, afc):
    print(teama + " vs. " + teamb)

# 带索引的列表迭代
teams = ["Packers", "49ers", "Ravens", "Patriots"]
for index, team in enumerate(teams):
    print(index, team)
