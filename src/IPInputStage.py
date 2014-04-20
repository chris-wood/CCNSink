import sys
import time
import BaseHTTPServer
import threading
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
		
		addr = self.client_address
		cmd = self.command
		path = self.path
		targetInterest = (stage.paramMap["NDN_URI_PREFIX"] + str(path)).replace("//", "/")
		print >> sys.stderr, (addr, cmd, path)

		# Build the message, send it out, and wait for a response
		myAddr = (stage.paramMap["HTTP_HOST"], stage.paramMap["HTTP_PORT"])
		msg = OutgoingMessage(addr, myAddr, targetInterest)
		stage.nextStage.put(msg)

		# TODO: replace what's written with raw bytes read from the pipeline
		self.wfile.write("Test")

class IPInputStage(PipelineStage, threading.Thread):
	def __init__(self, name, nextStage, paramMap):
		threading.Thread.__init__(self)
		global stage
		self.name = name
		self.nextStage = nextStage
		self.paramMap = paramMap
		stage = self # set the reference so the handler can refer back to this stage

	def run(self):
		# Setup the HTTP handler
		print >> sys.stderr, "HTTP server on: " + str(self.paramMap["HTTP_HOST"]) + ":" + str(self.paramMap["HTTP_PORT"])
		httpd = HTTPServer((self.paramMap["HTTP_HOST"], int(self.paramMap["HTTP_PORT"])), IPInputStageHTTPHandler)
		httpd.serve_forever()
		print >> sys.stderr, "Started server..."
