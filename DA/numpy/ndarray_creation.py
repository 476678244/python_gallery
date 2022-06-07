import numpy as np

my_ndarray = np.zeros([2,3], dtype=int)
print(my_ndarray)

my_ndarray = np.ones([2,3], dtype=int)
print(my_ndarray)

my_ndarray = np.full([2,3], 10, dtype=int)
print(my_ndarray)

my_ndarray = np.eye(3, dtype=int)
print(my_ndarray)

my_ndarray = np.diag([10, 20, 30, 40, 50])
print(my_ndarray)

my_ndarray = np.arange(1, 20, 3)
print(my_ndarray)
