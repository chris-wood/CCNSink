import sys
import threading
import pyccn
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

stage = None

class NDNOutputClosure(pyccn.Closure):
	def __init__(self, name, stage, table = None, paramMap = {}):
		self.handle = pyccn.CCN()
		self.version_marker = '\xfd'
		self.first_version_marker = self.version_marker
		self.last_version_marker = '\xfe\x00\x00\x00\x00\x00\x00'

	def upcall(self, kind, info):
		if (kind == pyccn.UPCALL_FINAL):
			return pyccn.RESULT_OK

		# TODO: any special handling should go here..

		return pyccn.RESULT_OK

	def dispatch(self, interest):
		co = self.handle.get(name = interest.name, template = interest)
		return co

class NDNOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, table = None, paramMap = {}):
		threading.Thread.__init__(self)
		global stage
		stage = self
		self.paramMap = paramMap
		self.table = table
		self.name = name
		self.queue = Queue()
		self.handle = NDNOutputClosure(name, self, table, paramMap)

	def put(self, msg):
		self.queue.put(msg)

	def buildInterest(self, msg):
		name = pyccn.Name(msg.dstName)
		interest = pyccn.Interest(name = name, minSuffixComponents = 1)
		return interest

	def run(self):
		self.running = True
		while (self.running):
			msg = self.queue.get()
			interest = self.buildInterest(msg)
			co = self.handle.dispatch(interest)
			if (self.table.updateIPEntry(msg.tag, co) == False):
				print >> sys.stderr, "FAILED TO UPDATE AN ENTRY"
			entry = stage.table.lookupIPEntry(msg.tag)
			entry[1].release() # release the lock now that we've updated the table


