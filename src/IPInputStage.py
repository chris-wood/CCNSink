import sys
import time
import BaseHTTPServer
from BaseHTTPServer import *
from PipelineStage import *

# Public reference to the stage instance for this pipeline (only one!)
stage = None

class IPInputStageHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_GET(self):
		global stage
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

		print("HERE")

		# TODO: send to the real pipeline stage (via queue?) so that it can be forwarded through the rest of the pipeline
		# block until response is generated... from NDN world

		# TODO: replace what's written with raw bytes read from the pipeline
		self.wfile.write("Hello World")

class IPInputStage(PipelineStage):
	def __init__(self, name, nextStage, paramMap = {}):
		self.name = name
		self.nextStage = nextStage
		stage = self # set the reference so the handler can refer back to this stage

		# Setup the HTTP handler
		print >> sys.stderr, "HTTP server on: " + str(paramMap["HTTP_HOST"]) + ":" + str(paramMap["HTTP_PORT"])
		httpd = HTTPServer((paramMap["HTTP_HOST"], 80), IPInputStageHTTPHandler)
		httpd.serve_forever()
		print >> sys.stderr, "Started server..."
