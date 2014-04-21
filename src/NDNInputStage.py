import time
import pyccn
import sys
from PipelineStage import *

class FlowController(pyccn.Closure):
	def __init__(self, stage, paramMap):
		self.prefix = pyccn.Name(paramMap["NDN_URI_ROOT"])
		self.handle = pyccn.CCN()
		self.cleanupTime = int(paramMap["NDN_CACHE_TIME"])
		self.stage = stage
		print(self.prefix)
		self.handle.setInterestFilter(self.prefix, self)

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

	def upcall(self, kind, info):
		global stage
		print "upcall baby"
		if kind in [pyccn.UPCALL_FINAL, pyccn.UPCALL_CONSUMED_INTEREST]:
			return pyccn.RESULT_OK

		if kind != pyccn.UPCALL_INTEREST:
			print >> sys.stderr, "Got weird upcall kind: %d" % kind
			return pyccn.RESULT_ERR

		# Extract the interest information and shove it into the pipeline
		print(info.Interest)
		baseOffset = len(stage.baseName.components)
		if (len(info.Interest.name.components) <= baseOffset):
			return pyccn.RESULT_ERR
		protocol = info.Interest.components[baseOffset]
		print("Protocol = " + str(protocol))

		# Construct a unique message for each of the supported protocols
		#TODO

		# Put the message in the PMT
		#TODO

		# myAddr = (stage.paramMap["HTTP_HOST"], stage.paramMap["HTTP_PORT"])
		# msg = OutgoingMessage(addr, myAddr, targetInterestName)
		# semaphore = multiprocessing.BoundedSemaphore(0)
		# stage.table.insertIPEntry(msg, semaphore)

		# Drop the message into the pipeline and wait for a response
		# stage.nextStage.put(msg)
		# semaphore.acquire()

		# Block and wait for response
		data = "NOT YET IMPLEMENTED"

		# Build output message and shoot it away
		content = self.buildContentObject(info.Interest, data)
		self.handle.put(content)

		return pyccn.RESULT_INTEREST_CONSUMED # if consumed else pyccn.RESULT_OK

class NDNInputStage(PipelineStage):
	def __init__(self, name, nextStage, table, paramMap):
		self.table = table

		# Set the base name
		self.baseName = pyccn.Name(paramMap["NDN_URI_ROOT"])

		fc = FlowController(self, paramMap)

