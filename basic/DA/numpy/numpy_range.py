import time

import numpy as np
# https://linux.cn/article-14160-1.html
my_list = np.arange(1, 1000000000)

print(len(my_list))

start = time.time()
my_list.min()
print('Time elapsed in milliseconds: ' + str((time.time() - start) * 1000))

start = time.time()
my_list.max()
print('Time elapsed in milliseconds: ' + str((time.time() - start) * 1000))




