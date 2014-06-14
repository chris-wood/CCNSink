import sys
import threading
import pyccn
import httplib
import logging
import time
from ftplib import FTP
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

# Setup logger info
logger = logging.getLogger('gateway')
hdlr = logging.FileHandler('./gateway.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

class HTTPOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, table, paramMap):
		threading.Thread.__init__(self)
		self.name = name
		self.table = table
		self.queue = Queue()

	def put(self, msg):
		self.queue.put(msg)

	def outputMessage(self, msg, protocol, entry):
		ip = msg.dstInfo[0]
		port = msg.dstInfo[1]
		conn = httplib.HTTPConnection(str(ip) + ":" + str(port))

		# Do time difference calcuiaton and shove it to the log file
		end = time.time()
		if (entry != None):
			diff = end - entry[3]
			logger.info('NDN-TO-IP: ' + str(diff))

		print >> sys.stderr, "Issuing GET to: " + str(ip) + ":" + str(port) + "/" + str(msg.dstName)
		
		conn.request("GET", str(msg.dstName))
		res = conn.getresponse()
		return res.read()

	def run(self):
		self.running = True
		while (self.running):
			tup = self.queue.get()
			protocol = tup[0]
			msg = tup[1]

			# Fetch the pending message table entry
			entry = self.table.lookupNDNEntry(msg.tag)

			# Output the message and get the response back
			res = self.outputMessage(msg, protocol, entry)
			if (res != None):
				if (self.table.updateNDNEntry(msg.tag, res) == False):
					print >> sys.stderr, "FAILED TO UPDATE AN ENTRY"
				entry[1].release() # release the lock now that we've updated the table
			else:
				print >> sys.stderr, "Error deliverying message: " + str(msg)

class TCPOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, table, paramMap):
		threading.Thread.__init__(self)
		self.name = name
		self.table = table
		self.queue = Queue()

	def put(self, msg):
		self.queue.put(msg)

	def outputMessage(self, msg, protocol):
		raise RuntimeError()

	def run(self):
		self.running = True
		while (self.running):
			tup = self.queue.get()
			print(tup)

class IPOutputStage(PipelineStage):
	def __init__(self, name, table, paramMap):
		self.queueMap = {}
		self.queueMap["http"] = HTTPOutputStage("HTTPOutputStage", table, paramMap)
		self.queueMap["http"].start()
		self.queueMap["tcp"] = TCPOutputStage("TCPOutputStage", table, paramMap)
		self.queueMap["tcp"].start()

	def put(self, tup):
		protocol = tup[0]
		msg = tup[1]
		if (protocol in self.queueMap):
			self.queueMap[protocol].put(tup)
		else:
			raise Exception("Invalid IP output protocol: " + str(protocol))
	
