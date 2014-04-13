import threading # should this really be a threaded class?... seems like it is only triggered asynchronously
import time
import pyccn

class NDNInputStage(PipelineStage, pyccn.Closure):

	def __init__(self, name, prefix, handle):
		PipelineStage.__init__(name)
		threading.Thread.__init__(self)
		self.prefix = pyccn.Name(prefix)
		self.handle = handle
		self.content_objects = []

		self.cleanup_time = 15 * 60 # keep responses for 15 min
		handle.setInterestFilter(self.prefix, self)

	def put(self, co):
		self.content_objects.append((time.time(), co))

	def dispatch(self, interest, elem):
		if time.time() - elem[0] > self.cleanup_time:
			return False
		elif elem[1].matchesInterest(interest):
			self.handle.put(elem[1])
			return False
		return True

	def upcall(self, kind, info):
		if kind in [pyccn.UPCALL_FINAL, pyccn.UPCALL_CONSUMED_INTEREST]:
			return pyccn.RESULT_OK

		if kind != pyccn.UPCALL_INTEREST:
			print("Got weird upcall kind: %d" % kind)
			return pyccn.RESULT_ERR

		f = lambda elem: self.dispatch(info.Interest, elem)

		new = []
		consumed = False
		for elem in self.content_objects:
			if consumed or f(elem):
				new.append(elem)
				continue
			consumed = True
		self.content_objects = new

		return pyccn.RESULT_INTEREST_CONSUMED if consumed else pyccn.RESULT_OK

