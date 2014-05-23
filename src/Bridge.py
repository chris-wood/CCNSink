import sys
import threading
import httplib
import time
import json
import asyncore
import socket
from multiprocessing import Queue

class BridgeHandler(asyncore.dispatcher_with_send):
	def __init__(self):
		self.buffer = []

	# self.request is the TCP socket connected to the client
	def handleData(self): 
		data = self.recv(8192)
		if data:
			self.send(data)

class BridgeServer(asyncore.dispatcher):
	def __init__(self, host, port):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.listen(5)

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			print 'Incoming connection from %s' % repr(addr)
			handler = BridgeHandler(sock)

class Bridge(threading.Thread):
	def __init__(self, paramMap):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}
		self.socketMap = {}
		self.connected = False
		server = BridgeServer(self.paramMap["LOCALHOST"], self.paramMap["BRIDGE_LOCAL_PORT"])

	def run(self):
		self.running = True
		asyncore.loop()

		# Loop until we're told to quit
		while (self.running):
			# Try to connect first
			if (not self.connected):
				self.connectToServer()

			# If connected, send the server a heartbeat message and update our gateway list
			if (self.connected): 
				self.sendHeartbeat()
				self.updateGateways()

			# Sleep it off man...
			time.sleep(int(self.paramMap["BRIDGE_SERVER_UPDATE_FREQ"]))

	def connectToServer(self):
		conn = httplib.HTTPConnection(self.paramMap["BRIDGE_SERVER_ADDRESS"])
		resp = conn.request("POST", "/connect", None, None)
		if (int(resp.status) == 200):
			self.connected = True

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

	def getGateways(self):
		return gateways

	def lookupPrefix(self, prefix):
		if (self.prefixGatewayMap.contains(prefix)):
			return self.prefixGatewayMap[prefix]
		else:
			return None

	# Messages are sent as follows: |name length|name|
	def sendInterest(self, interest, targetAddress):
		sock = None
		if (not self.socketMap.contains(targetAddress)):
			print("TODO: establish a socket connection to the address")
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(targetAddress) # address is a tuple, e.g., targetAddress = ("www.python.org", 80)
			self.socketMap[targetAddress] = sock
		else:
			sock = self.socketMap[targetAddress]
		
		# Send the message
		nameLen = len(interest)
		sock.send(nameLen)
		sock.send(interest)

	def retrieveContent(self, content, sourceAddress):
		print("TODO")