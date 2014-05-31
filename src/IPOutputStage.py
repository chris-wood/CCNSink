import sys
import threading
import pyccn
import httplib
from ftplib import FTP
from multiprocessing import Queue
from PipelineStage import *
from OutgoingMessage import *

class HTTPOutputStage(PipelineStage, threading.Thread):
	def __init__(self, name, table, paramMap):
		threading.Thread.__init__(self)
		self.name = name
		self.table = table
		self.queue = Queue()

	def put(self, msg):
		self.queue.put(msg)

	def outputMessage(self, msg, protocol):
		ip = msg.dstInfo[0]
		port = msg.dstInfo[1]
		conn = httplib.HTTPConnection(str(ip) + ":" + str(port))

		print >> sys.stderr, "Issuing GET to: " + str(ip) + ":" + str(port) + "/" + str(msg.dstName)
		
		conn.request("GET", str(msg.dstName))
		res = conn.getresponse()
		return res.read()

	def run(self):
		self.running = True
		while (self.running):
			tup = self.queue.get()
			print >> sys.stderr, "HTTPOutputStage processing a message..."
			protocol = tup[0]
			msg = tup[1]

			# Output the message and get the response back
			res = self.outputMessage(msg, protocol)
			if (res != None):
				if (self.table.updateNDNEntry(msg.tag, res) == False):
					print >> sys.stderr, "FAILED TO UPDATE AN ENTRY"
				entry = self.table.lookupNDNEntry(msg.tag)
				entry[1].release() # release the lock now that we've updated the table
			else:
				print >> sys.stderr, "Error deliverying message: " + str(msg)

# class FTPOutputStage(PipelineStage, threading.Thread):
# 	def __init__(self, name, table, paramMap):
# 		threading.Thread.__init__(self)
# 		self.name = name
# 		self.table = table
# 		self.queue = Queue()

# 	def put(self, msg):
# 		self.queue.put(msg)

# 	def outputMessage(self, msg, protocol):
# 		raise RuntimeError()
# 		# ip = msg.dstInfo[0]
# 		# port = msg.dstInfo[1]
# 		# target = str(ip) + ":" + str(port)

# 		# # Connect to the server and login
# 		# ftp = FTP(target)
# 		# ftp.login()

# 		# # Fetch the file and pipe its contents back as content
# 		# f = open("ftp-tmp", "wb")
# 		# ftp.retrbinary("RETR " + file,f.write)
# 		# f.close
# 		# contents = []
# 		# with open("myfile", "rb") as f:
# 		# 	byte = f.read(1)
# 		# 	contents.append(byte)
# 		# 	while byte != "":
#   #       		byte = f.read(1)
#   #       		contents.append(byte)
#   #       ba = bytearray(h.decode("hex") for h in contents)
# 		# return ba

# 	def run(self):
# 		self.running = True
# 		while (self.running):
# 			tup = self.queue.get()

# 			print >> sys.stderr, "FTPOutputStage processing a message..."
# 			protocol = tup[0]
# 			msg = tup[1]

# 			# Output the message and get the response back
# 			res = self.outputMessage(msg, protocol)
# 			if (res != None):
# 				if (self.table.updateNDNEntry(msg.tag, res) == False):
# 					print >> sys.stderr, "FAILED TO UPDATE AN ENTRY"
# 				entry = self.table.lookupNDNEntry(msg.tag)
# 				entry[1].release() # release the lock now that we've updated the table
# 			else:
# 				print >> sys.stderr, "Error deliverying message: " + str(msg)

class IPOutputStage(PipelineStage):
	def __init__(self, name, table, paramMap):
		self.queueMap = {}
		self.queueMap["http"] = HTTPOutputStage("HTTPOutputStage", table, paramMap)
		self.queueMap["ftp"] = FTPOutputStage("FTPOutputStage", table, paramMap)

	# TODO: add protocol param here, and then add it to the appropriate queue (one thread per queue for ^ throughput)
	def put(self, msg):
		if (msg.protocol in self.queueMap):
			self.queueMap[msg.protocol].put(msg)
		else:
			raise Exception("Invalid IP output protocol: " + str(msg.protocol))
	
