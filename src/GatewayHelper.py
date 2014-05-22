import sys
import threading
import httplib
import time
import json
from multiprocessing import Queue

class HTTPOutputStage(threading.Thread):
	def __init__(self, paramMap):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}

	def run(self):
		self.running = True
		while (self.running):
			# Send the server a heartbeat message
			self.sendHeartbeat()

			# Update the list of known gateways
			self.updateGateways()

			# Sleep it off man...
			time.sleep(int(self.paramMap["BRIDGE_SERVER_UPDATE_FREQ"]))

	def sendHeartbeat(self):
		conn = httplib.HTTPConnection(self.paramMap["BRIDGE_SERVER_ADDRESS"])
		conn.request("POST", "/heartbeat", None, None)

	def updateGateways(self):
		conn = httplib.HTTPConnection(self.paramMap["BRIDGE_SERVER_ADDRESS"])
		resp = conn.request("GET", "/list-gateways", None, None)
		dic = json.loads(resp)
		self.gateways = []
		for gateway in dic["gateways"]:
			self.gateways.append(gateway) # gateway should be the address


