import threading # should this really be a threaded class?... seems like it is only triggered asynchronously
import time
import BaseHTTPServer

class NDNInputStageHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

		# TODO: send to the real pipeline stage (via queue?) so that it can be forwarded through the rest of the pipeline
		# block until response is generated... from NDN world

		# TODO: replace what's written with raw bytes read from the pipeline
		self.wfile.write("Hello World")

class NDNInputStage(PipelineStage):
	def __init__(self, name, paramMap = {}):
		self.name = name

		# Setup the HTTP handler
		print >> sys.stderr, "HTTP server on: " + str(paramMap["HTTP_HOST"]) + ":" + str(paramMap["HTTP_PORT"])
		server_class = BaseHTTPServer.HTTPServer
		httpd = server_class((paramMap["HTTP_HOST"], paramMap["HTTP_PORT"]), NDNInputStageHTTPHandler)
