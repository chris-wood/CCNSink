import time
import sys
import pyccn

class NDNOutputClosure(pyccn.Closure):
	def __init__(self):
		self.handle = pyccn.CCN()
		self.version_marker = '\xfd'
		self.first_version_marker = self.version_marker
		self.last_version_marker = '\xfe\x00\x00\x00\x00\x00\x00'

	def upcall(self, kind, info):
		if (kind == pyccn.UPCALL_FINAL):
			return pyccn.RESULT_OK
		return pyccn.RESULT_OK

	def dispatch(self, interest):
		co = self.handle.get(name = interest.name, template = interest)
		return co

handle = NDNOutputClosure()

prefix = str(sys.argv[1])
n = int(sys.argv[2])
data = []
for i in range(n):
	start = time.time()
	name = pyccn.Name(prefix) #+ "/?nonce=" + str(i))
	interest = pyccn.Interest(name = name, minSuffixComponents = 1)
	print(interest.name)
	co = handle.handle.get(name = interest.name, template = interest)
	print(co.content)
	end = time.time()
	data.append((n, str(interest.name), co.content, (end - start)))

total = 0
for i in range(n):
	t = float(data[i][3])
	total = total + t
	print(str(t) + ","),
print("")
print(float(total) / float(n))
