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
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		
		# Extract the relevant information needed to build the interest
		addr = self.client_address
		cmd = self.command
		path = self.path
		targetInterestName = (stage.paramMap["NDN_URI_PREFIX"] + str(path)).replace("//", "/")

		# Build the message and drop it into the table
		myAddr = (stage.paramMap["HTTP_HOST"], stage.paramMap["HTTP_PORT"])
		msg = OutgoingMessage(addr, myAddr, targetInterestName, "http")
		semaphore = multiprocessing.BoundedSemaphore(0)
		stage.table.insertIPEntry(msg, semaphore)

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
		print >> sys.stderr, "HTTP server on: " + str(self.paramMap["HTTP_HOST"]) + ":" + str(self.paramMap["HTTP_PORT"])
		httpd = HTTPServer((self.paramMap["HTTP_HOST"], int(self.paramMap["HTTP_PORT"])), IPInputStageHTTPHandler)
		httpd.serve_forever()
		print >> sys.stderr, "Started server..."

