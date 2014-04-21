import time
import pyccn
import sys
from pyccn import _pyccn, Key, ContentObject
from PipelineStage import *

class FlowController(pyccn.Closure):
	def __init__(self, prefix, handle, paramMap):
		self.prefix = pyccn.Name(prefix)
		self.handle = handle
		self.content_objects = []
		self.cleanup_time = int(paramMap["NDN_CACHE_TIME"])
		handle.setInterestFilter(self.prefix, self)

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
		if (time.time() - elem[0]) > self.cleanup_time:
			return False
		elif (elem[1].matchesInterest(interest)):
			self.handle.put(elem[1])
			return False
		return True

	def upcall(self, kind, info):
		if kind in [pyccn.UPCALL_FINAL, pyccn.UPCALL_CONSUMED_INTEREST]:
			return pyccn.RESULT_OK

		if kind != pyccn.UPCALL_INTEREST:
			print >> sys.stderr, "Got weird upcall kind: %d" % kind
			return pyccn.RESULT_ERR

		# Extract the interest information and shove it into the pipeline
		print(info.Interest)

		# Block and wait for response
		#TODO
		data = "TEST"

		# Build output message
		content = self.buildContentObject(info.Interest, data)

		return pyccn.RESULT_INTEREST_CONSUMED if consumed else pyccn.RESULT_OK

class NDNInputStage(PipelineStage):
	def __init__(self, name, nextStage, table, paramMap):
		self.table = table
		fc = FlowController(paramMap["NDN_URI_ROOT"], pyccn.CCN(), paramMap)

