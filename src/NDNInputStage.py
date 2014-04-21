import time
import pyccn
import sys
import threading
import multiprocessing
from PipelineStage import *
from OutgoingMessage import *

class NDNHandle(pyccn.Closure):
	def __init__(self, stage, paramMap):
		self.paramMap = paramMap
		self.stage = stage
		self.baseOffset = len(self.stage.baseName.components)
		self.prefix = pyccn.Name(paramMap["NDN_URI_ROOT"])
		self.cleanupTime = int(paramMap["NDN_CACHE_TIME"])
		self.handle = pyccn.CCN()

	def run(self):
		self.handle.setInterestFilter(self.prefix, self)
		self.handle.run(-1)

	def buildContentObject(self, name, content):
		key = pyccn.CCN.getDefaultKey()
		keylocator = pyccn.KeyLocator(key)

		# Name
		co_name = pyccn.Name(name).appendSegment(0)

		# SignedInfo
		si = pyccn.SignedInfo()
		si.type = pyccn.CONTENT_DATA
		si.finalBlockID = pyccn.Name.num2seg(0)
		si.publisherPublicKeyDigest = key.publicKeyID
		si.keyLocator = keylocator

		# ContentObject
		co = pyccn.ContentObject()
		co.content = content
		co.name = co_name
		co.signedInfo = si

		co.sign(key)
		return co

	def dispatch(self, interest, elem):
		if (time.time() - elem[0]) > self.cleanupTime:
			return False
		elif (elem[1].matchesInterest(interest)):
			self.handle.put(elem[1])
			return False
		return True

	def buildMessage(self, name, protocol):
		if (protocol == "http"):
			srcInfo = (self.paramMap["HTTP_HOST"], self.paramMap["HTTP_PORT"])
			dstInfo = (name.components[self.baseOffset + 1], name.components[self.baseOffset + 2])
			path = str(name.components[self.baseOffset + 3:])
			if (len(path[0] == 0)):
				path = "/" # workaround
			msg = OutgoingMessage(srcInfo, dstInfo, path)
			return msg
		else:
			return None

	def upcall(self, kind, info):
		if kind in [pyccn.UPCALL_FINAL, pyccn.UPCALL_CONSUMED_INTEREST]:
			return pyccn.RESULT_OK

		if kind != pyccn.UPCALL_INTEREST:
			print >> sys.stderr, "Got weird upcall kind: %d" % kind
			return pyccn.RESULT_ERR

		# Extract the interest information and shove it into the pipeline
		print(info.Interest)
		if (len(info.Interest.name.components) <= self.baseOffset):
			print >> sys.stderr, "Error: No protocol specified"
			return pyccn.RESULT_ERR
		protocol = str(info.Interest.name.components[self.baseOffset]).lower()

		# Construct a unique message for each of the supported protocols
		msg = self.buildMessage(info.Interest.name, protocol)
		if (msg == None):
			msg = "Error: Unable to build IP message"
			print >> sys.stderr, msg
			content = self.buildContentObject(info.Interest.name, msg)
			self.handle.put(content)
			return pyccn.RESULT_ERR

		# Put the message in the PMT, throw it to the next stage, and then block
		semaphore = multiprocessing.BoundedSemaphore(0)
		self.stage.table.insertNDNEntry(msg, semaphore)
		tup = (protocol, msg)
		self.stage.nextStage.put(tup)
		semaphore.acquire()

		# Acquire the content, and write it back out
		entry = self.stage.table.lookupNDNEntry(msg.tag)
		data = None
		if (entry != None):
			self.stage.table.clearNDNEntry(msg.tag)
			content = entry[2]
			data = content
			content = self.buildContentObject(info.Interest.name, data)
			self.handle.put(content)
			return pyccn.RESULT_INTEREST_CONSUMED
		else:
			data = "Error: internal gateway error."
			content = self.buildContentObject(info.Interest.name, data)
			self.handle.put(content)
			return pyccn.RESULT_ERR

class NDNInputStage(PipelineStage):
	def __init__(self, name, nextStage, table, paramMap):
		self.table = table
		self.nextStage = nextStage

		# Set the base name
		self.baseName = pyccn.Name(paramMap["NDN_URI_ROOT"])

		# Create and start the flow controller
		fc = NDNHandle(self, paramMap)
		fc.run()

