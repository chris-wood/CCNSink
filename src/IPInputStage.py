import sys
import time
import BaseHTTPServer
import threading
import multiprocessing
from PendingMessageTable import *
from BaseHTTPServer import *
from PipelineStage import *
from OutgoingMessage import *

# Public reference to the stage instance for this pipeline (only one!)
stage = None

class IPInputStageHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_GET(self):
		global stage
		start = time.time()
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		
		# Extract the relevant information needed to build the interest
		addr = self.client_address
		cmd = self.command
		path = self.path
		targetInterestName = (stage.paramMap["NDN_URI_PREFIX"] + str(path)).replace("//", "/")

		# Build the message and drop it into the table
		myAddr = (stage.paramMap["PUBLIC_IP"], stage.paramMap["HTTP_PORT"])
		msg = OutgoingMessage(addr, myAddr, targetInterestName, "http")
		semaphore = multiprocessing.BoundedSemaphore(0)
		stage.table.insertIPEntry(msg, semaphore, start)

		# Drop the message into the pipeline and wait for a response
		stage.nextStage.put(msg)
		semaphore.acquire()

		# Acquire the content, and write it back out
		entry = stage.table.lookupIPEntry(msg.tag)
		if (entry != None):
			stage.table.clearIPEntry(msg.tag)
			content = entry[2]
			self.wfile.write(str(content))
		else:
			self.wfile.write("Error: internal gateway error.")

# this is the gateway tcp server, NOT the bridge tcp server
class IPTCPServer(threading.Thread):
	def __init__(self, name, nextStage, paramMap):
		threading.Thread.__init__(self)
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.bind((socket.gethostname(), int(paramMap["TCP_PORT"])))
		self.serversocket.listen(int(paramMap["TCP_LISTEN"]))
		self.paramMap = paramMap

	def run(self):
		self.running = True
		while (self.running):
			(clientsocket, address) = self.serversocket.accept()
			ct = client_thread(self.paramMap, clientsocket)
			print >> sys.stderr, "Spawning handler thread..."
			ct.run()

class IPTCPSocketHandler(threading.Thread):
	def __init__(self, paramMap, nextStage, socket):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.nextStage = nextStage
		self.socket = socket

	def run(self):
		self.running = True
		MSGLEN = int(self.paramMap["TCP_MSGLEN"])
		while (self.running):
			chunks = [] # maintain state...
			bytes_recd = 0
			pathchunks = [] # read until END_OF_PATH character is encountered
			self.pathEaten = False
			while bytes_recd < MSGLEN:
				chunk = self.socket.recv(min(MSGLEN - bytes_recd, 2048))
				if (chunk == b''):
					raise RuntimeError("Socket connection broken")

				# Maintain the byte stream state 
				chucks.append(chunk)
				bytes_recd = bytes_recd + len(chunk)

				# Check to see if we're still reading the path
				if (self.pathEaten):
					# Send the chunk to the application
					interest = self.buildInterest(chunk)
					# myAddr = (stage.paramMap["PUBLIC_IP"], stage.paramMap["HTTP_PORT"])
					# msg = OutgoingMessage(addr, myAddr, targetInterestName, "http")
					# self.nextStage.put(msg)
				else:
					pathchunks.append(chunk)
					for i in range(len(chunk)):
						EOF = int(self.paramMap["TCP_END_OF_PATH_CHAR"], 16)
						if (int(chunk[i]) == EOF):
							self.pathEaten = True
							self.setPath(pathchunks)
							break

	# TODO: how are the string bytes encoded?
	def setPath(self, pathBytes):
		raise RuntimeError("not yet implemented")

	# TODO: how to decode the first couple chunks as the path?
	def buildInterest(self, chunk):
		# Extract the relevant information needed to build the interest
		# addr = self.client_address
		# cmd = self.command
		path = self.path
		targetInterestName = (stage.paramMap["NDN_URI_PREFIX"] + str(path)).replace("//", "/")

		# Build the message and drop it into the table
		# myAddr = (stage.paramMap["PUBLIC_IP"], stage.paramMap["HTTP_PORT"])
		# msg = OutgoingMessage(addr, myAddr, targetInterestName, "http")
		# semaphore = multiprocessing.BoundedSemaphore(0)
		# stage.table.insertIPEntry(msg, semaphore)
		return targetInterestName

class IPInputStage(PipelineStage, threading.Thread):
	def __init__(self, name, nextStage, table, paramMap):
		threading.Thread.__init__(self)
		global stage
		self.name = name
		self.nextStage = nextStage
		self.paramMap = paramMap
		self.table = table
		stage = self # set the reference so the handler can refer back to this stage

	def run(self):
		# Setup the HTTP handler
		print >> sys.stderr, "HTTP server on: " + str(self.paramMap["PUBLIC_IP"]) + ":" + str(self.paramMap["HTTP_PORT"])
		httpd = HTTPServer((self.paramMap["PUBLIC_IP"], int(self.paramMap["HTTP_PORT"])), IPInputStageHTTPHandler)
		httpd.serve_forever()
		print >> sys.stderr, "Started server..."

