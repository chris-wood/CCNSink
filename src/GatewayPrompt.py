import sys
import threading
import time

""" Separate threaded class that handles user input at runtime to control the gateway.
"""
class GatewayPrompt(threading.Thread):

	""" Construct the gateway using parameters from the paramMap.
	"""
	def __init__(self, gateway):
		threading.Thread.__init__(self)
		self.gateway = gateway

	def run(self):
		self.running = True
		while (self.running):
			line = ""
			try:
				print("> "),
				line = sys.stdin.readline()
			except KeyboardInterrupt:
				break
			if (len(line.strip()) > 0):
				self.parseInput(line.strip())

	def parseInput(self, usrInput):
		print("Parsing: " + usrInput)
		if (usrInput == "exit"):
			print("?> Killing all services...")
			self.gateway.stop()
			self.running = False
		else:
			print("?> Command " + str(usrInput) + " unknown")
			self.printHelp()

	def printHelp(self):
		print("TODO")

	def 