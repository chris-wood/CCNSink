import time
import pyccn
import sys
import threading
import multiprocessing
from Bridge import *
from PipelineStage import *
from OutgoingMessage import *

class NDNHandle(pyccn.Closure):
	def __init__(self, stage, paramMap):
		self.paramMap = paramMap
		self.stage = stage
		self.baseOffset = len(self.stage.baseName.components)
		self.prefix = pyccn.Name(paramMap["NDN_URI_ROOT"])
		self.prefixAll = pyccn.Name(paramMap["NDN_URI_ROOT_ALL"])
		self.cleanupTime = int(paramMap["NDN_CACHE_TIME"])
		self.handle = pyccn.CCN()

	def run(self):
		self.handle.setInterestFilter(self.prefix, self)
		self.handle.setInterestFilter(self.prefixAll, self)
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
			srcInfo = (self.paramMap["PUBLIC_IP"], self.paramMap["HTTP_PORT"])
			dstInfo = (name.components[self.baseOffset + 1], name.components[self.baseOffset + 2])
			path = name.components[self.baseOffset + 3:] # e.g., skip over protocol, dst IP, dst port, and go to 0 -> /gateway/http/google.com/80/0
			if (len(path) == 0):
				path = ["/"] # workaround
			realPath = ""
			for c in path:
				realPath = c + "/"
			print(realPath)
			msg = OutgoingMessage(srcInfo, dstInfo, realPath, protocol)
			return msg
		# elif (protocol == "tcp"):
		# 	# srcInfo = (self.paramMap["HTTP_HOST"], self.paramMap["HTTP_PORT"])
		# 	# dstInfo = (name.components[self.baseOffset + 1], name.components[self.baseOffset + 2])
		# 	# path = str(name.components[self.baseOffset + 3:])
		# 	# if (len(path[0] == 0)):
		# 	# 	path = "/" # workaround
		# 	# msg = OutgoingMessage(srcInfo, dstInfo, path, protocol)
		# 	# return msg
		# 	return None
		else: # invalid case
			raise RuntimeError()

	def forwardGeneralInterest(self, name):
		bridge = self.stage.bridge
		prefixMatch = False
		match = None
		content = None
		for i in range(1, len(name.components)):
			prefix = ""
			for j in range(0, i - 1):
				prefix = prefix + name.components[j] + "/"
			prefix = prefix + name.components[i]
			(match, address) =  bridge.lookupPrefix(prefix) # address is a subset of bridge.gateways
			if (match != None):
				prefixMatch = True
				content = bridge.sendInterest(name, address)

		if (not prefixMatch): # broadcast to all gateways maintained by the bridge
			data = []
			for gateway in bridge.getGateways():
				print >> sys.stderr, "Gateway = " + str(gateway) # this is the address of the gateway
				data.append(bridge.sendInterest(name, gateway))
			for c in data:
				if (c != None): # pick the first one that returned something meaningful
					content = c
					break
		return content

	def upcall(self, kind, info):
		start = time.time()
		if kind in [pyccn.UPCALL_FINAL, pyccn.UPCALL_CONSUMED_INTEREST]:
			return pyccn.RESULT_OK

		if kind != pyccn.UPCALL_INTEREST:
			print >> sys.stderr, "Got weird upcall kind: %d" % kind
			return pyccn.RESULT_ERR

		# Extract the interest information and shove it into the pipeline
		print(info.Interest)
		if (len(info.Interest.name.components) <= self.baseOffset):
			print >> sys.stderr, "Error: No protocol specified in name: " + str(info.Interest.name)
			content = self.forwardGeneralInterest(info.Interest.name)
			self.handle.put(content)
			return pyccn.RESULT_OK
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
		self.stage.table.insertNDNEntry(msg, semaphore, start)
		tup = (protocol, msg)
		print("inserting msg to next stage")
		self.stage.nextStage.put(tup)
		semaphore.acquire()

		# Acquire the content, and write it back out
		entry = self.stage.table.lookupNDNEntry(msg.tag)
		data = None
		if (entry != None):
			self.stage.table.clearNDNEntry(msg.tag)
			#data = entry[2]
			data = "test...."
			co = self.buildContentObject(info.Interest.name, data)
			print(co.content)
			self.handle.put(co)
			return pyccn.RESULT_INTEREST_CONSUMED
		else:
			data = "Error: internal gateway error."
			content = self.buildContentObject(info.Interest.name, data)
			self.handle.put(content)
			return pyccn.RESULT_ERR

class NDNInputStage(PipelineStage):
	def __init__(self, name, nextStage, ndnOutputStage, table, paramMap):
		self.table = table
		self.nextStage = nextStage
		self.baseName = pyccn.Name(paramMap["NDN_URI_ROOT"])
		self.bridge = Bridge(paramMap, ndnOutputStage)
		self.ndnHandler = NDNHandle(self, paramMap)

		# Create and start the input handler and gateway helper
		self.bridge.start()
		self.ndnHandler.run()

