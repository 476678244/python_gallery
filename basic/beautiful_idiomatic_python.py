# https://gist.github.com/0x4D31/f0b633548d8e0cfb66ee3bea6a0deff9
import threading
from collections import defaultdict, deque

for i in range(6):
    print(i ** 2)

colors = ['red', 'green', 'blue', 'yellow']
for color in reversed(colors):
    print(color)

for i, color in enumerate(colors):
    print(i, '--->', color)

names = ['raymond', 'rachel', 'matthew']
for name, color in zip(names, colors):
    print(name, '--->', color)

print(sorted(colors, key=len))


def find(seq, target):
    for i, value in enumerate(seq):
        if value == target:
            break
    else:
        return -1
    return i


print(find(colors, 'blue'))

d = {'matthew': 'blue', 'rachel': 'green', 'raymond': 'red'}
for k, v in d.items():
    print(k, '--->', v)

d = {}
for color in colors:
    d[color] = d.get(color, 0) + 1

# Slightly more modern but has several caveats, better for advanced users
# who understand the intricacies
d = defaultdict(int)
for color in colors:
    d[color] += 1
print(d)

d = defaultdict(list)
for name in names:
    key = len(name)
    d[key].append(name)
print(d)

p = 'Raymond', 'Hettinger', 0x30, 'python@example.com'

fname, lname, age, email = p


def fibonacci(n):
    x, y = 0, 1
    for i in range(n):
        print(x)
        x, y = y, x + y


fibonacci(5)

names = deque(['raymond', 'rachel', 'matthew', 'roger',
               'betty', 'melissa', 'judith', 'charlie'])

# More efficient with deque
del names[0]
names.popleft()
names.appendleft('mark')
print(names)

# Make a lock
lock = threading.Lock()
with lock:
    print('Critical section 1')
    print('Critical section 2')
