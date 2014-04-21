import sys
import threading
import pyccn
import httplib
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

class IPOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, table, paramMap):
		threading.Thread.__init__(self)
		self.name = name
		self.table = table
		self.queue = Queue()

	# TODO: add protocol param here, and then add it to the appropriate queue (one thread per queue for ^ throughput)
	def put(self, msg):
		self.queue.put(msg)

	def outputMessage(self, msg, protocol):
		if (protocol == "http"):
			ip = msg.dstInfo[0]
			port = msg.dstInfo[1]
			conn = httplib.HTTPConnection(str(ip) + ":" + str(port))

			print >> sys.stderr, "Issuing GET to: " + str(ip) + ":" + str(port) + "/" + str(msg.dstName)
			
			conn.request("GET", str(msg.dstName))
			res = conn.getresponse()
			return res.read()
		else:
			print >> sys.stderr, "Error: Unsupported application-layer protocol: " + str(protocol)

	def run(self):
		self.running = True
		while (self.running):
			tup = self.queue.get()
			print >> sys.stderr, "IPOutputStage processing a message..."
			protocol = tup[0]
			msg = tup[1]

			# Output the message and get the response back
			res = self.outputMessage(msg, protocol)
			if (self.table.updateNDNEntry(msg.tag, res) == False):
				print >> sys.stderr, "FAILED TO UPDATE AN ENTRY"
			entry = self.table.lookupNDNEntry(msg.tag)
			entry[1].release() # release the lock now that we've updated the table
