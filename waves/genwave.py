#! python3
from pylab import *

if False:    # 正弦波
    x = arange(300) / 300 * np.pi * 2
    y = sin(x)

    y = y * 2047 + 2048
    y = y.astype(int)

if False:    # 方波
    x = range(100)
    y = [0] * 50 + [4095] * 50

if True:    # 三角波
    x = range(100)
    y = arange(50) / 50 * 4095
    y = list(y.astype(int))
    y = y + y[::-1]

for i, z in enumerate(y):
    if i % 20 == 0:
        print()

    print(f'{z:03X}, ', end='')
print()

plot(x, y)
show()
