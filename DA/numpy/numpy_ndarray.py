import numpy as np

my_ndarray = np.array([1, 2, 3, 4, 5])
print(my_ndarray)
print(type(my_ndarray))
print(np.shape(my_ndarray))
print(my_ndarray.size)

my_ndarray2 = np.array([(1, 2, 3), (4, 5, 6)])
print(np.shape(my_ndarray2))
print(my_ndarray2.dtype)

my_ndarray2 = np.array([1, 2.0, 3])
print(my_ndarray2)
print(my_ndarray2.dtype)

my_ndarray2 = np.array([1, '2', 3])
print(my_ndarray2)
print(my_ndarray2.dtype)