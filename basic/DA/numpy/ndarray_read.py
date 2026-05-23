import numpy as np

my_ndarray = np.arange(1, 20, 3)
print(my_ndarray[0])
print(my_ndarray[-1])

print(my_ndarray[:])
print(my_ndarray[2:4])
print(my_ndarray[5:6])
print(my_ndarray[:-1])

my_ndarray[-1:] = 100
print(my_ndarray)

my_ndarray2 = np.array([(1, 2, 3), (4, 5, 6)])
print(my_ndarray2)
print(my_ndarray2[0:2,1:3])


my_ndarray = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
my_ndarray2 = my_ndarray[my_ndarray > 5]
print(my_ndarray2)
my_ndarray2 = my_ndarray[my_ndarray % 2 == 0]
print(my_ndarray2)