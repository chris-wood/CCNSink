import httplib
import sys
import time

conn = httplib.HTTPConnection(sys.argv[1])
prefix = str(sys.argv[2])
n = int(sys.argv[3])
data = []
for i in range(n):
	url = prefix + "/" + str(i)
	start = time.time()
	conn.request("GET", url)
	resp = conn.getresponse()
	end = time.time()
	data.append((n, url, resp, (end - start)))

total = 0
for i in range(n):
	t = float(data[i][3])
	total = total + t
	print(str(t) + ","),
print("")
print(float(total) / float(n))