import sys
import threading
import pyccn
import time
import logging
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

stage = None

# Setup logging redirection
logger = logging.getLogger('gateway')
hdlr = logging.FileHandler('./gateway.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

class NDNOutputClosure(pyccn.Closure):
	def __init__(self, name, stage, table = None, paramMap = {}):
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

class NDNFetcher(threading.Thread):
	def __init__(self, stage, msg):
		threading.Thread.__init__(self)
		self.stage = stage
		self.msg = msg

	def run(self):
		# Build the interest
		msg = self.msg
		stage = self.stage
		interest = stage.buildInterest(msg)

		# Perform time difference calc and log it
		end = time.time()
		entry = stage.table.lookupIPEntry(msg.tag) # entry is (msg, log, None, time)
		print(entry)
		if (entry != None):
			diff = end - entry[3]
			logger.info('IP-TO-NDN: ' + str(diff))

		# Shoot out the interest and wait for the response
		co = stage.handle.dispatch(interest)
		content = None
		if (co != None):
			content = co.content
		else:
			logger.error("NDN interest failed (None returned): " + str(msg))
		if (stage.table.updateIPEntry(msg.tag, content) == False):
			logger.error("Failed to update an entry")
		entry[1].release() # release the lock now that we've updated the table

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
			fetcher = NDNFetcher(self, msg)
			fetcher.run()

