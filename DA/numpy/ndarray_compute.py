import numpy as np

my_ndarray = np.array([1, 2, 3, 4, 5])
my_ndarray2 = np.array([6, 7, 8, 9, 10])

print(my_ndarray2 + my_ndarray)
print(my_ndarray2 - my_ndarray)
print(my_ndarray2 * my_ndarray)
print(my_ndarray2 / my_ndarray)

print(my_ndarray + 10)
print(my_ndarray - 10)
print(my_ndarray * 10)
print(my_ndarray / 10)

my_ndarray = np.array([3, 1, 2, 5, 4])
my_ndarray.sort()
print(my_ndarray)

my_ndarray = np.array([3, 1, 2, 5, 4])
print(np.sort(my_ndarray))
print(my_ndarray)