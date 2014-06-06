import os
import sys
import random

d = float(sys.argv[2])
times = []
total = 0.0
for i in range(int(sys.argv[1])):
	r = random.random() - 0.5
	dd = (d * r) + d
	total = total + dd
	times.append(dd)
	print(str(dd) + ","),
mean = total / float(sys.argv[1])
print(mean)