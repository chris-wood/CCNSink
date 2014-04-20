import sys
import threading
import pyccn
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

def callback(kind, info):
	print("Name: " + str(info.ContentObject.name))
	print(info.ContentObject.content)

class NDNOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, nextStage = None, table, paramMap = {}):
		threading.Thread.__init__(self)
		self.table = table
		self.handle = pyccn.CCN()
		self.name = name
		self.nextStage = nextStage
		self.queue = Queue()

	def put(self, msg):
		self.queue.put(msg)

	def upcall(self, kind, info):
		if (kind == pyccn.UPCALL_FINAL):
			return pyccn.RESULT_OK
		self.callback(kind, info)
		return pyccn.RESULT_OK

	def buildInterest(self, msg):
		name = pyccn.Name([msg.dstName])
		print(name)
		interest = pyccn.Interest(name = name, minSuffixComponents = 1)
		return interest

	def run(self):
		self.running = True
		while (self.running):
			msg = self.queue.get()
			interest = self.buildInterest(msg)
			print >> sys.stderr, "Putting: " + str(interest)
			co = self.handle.get(name = interest.name, template = interest)

