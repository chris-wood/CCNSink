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

class BridgeServer(asyncore.dispatcher, threading.Thread):
	def __init__(self, host, port):
		asyncore.dispatcher.__init__(self)
		threading.Thread.__init__(self)
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

	def run(self):
		asyncore.loop()

class Bridge(threading.Thread):
	def __init__(self, paramMap):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}
		self.socketMap = {}
		self.connected = False
		self.server = BridgeServer(self.paramMap["LOCALHOST"], self.paramMap["BRIDGE_LOCAL_PORT"])

	def run(self):
		self.running = True
		self.server.start()

		# Establish long-term connection
		print >> sys.stderr, "Establishing connection with directory: " + str(self.paramMap["BRIDGE_SERVER_ADDRESS"])
		self.conn = httplib.HTTPConnection(self.paramMap["BRIDGE_SERVER_ADDRESS"])

		# Loop until we're told to quit
		print >> sys.stderr, "Running bridge"
		while (self.running):
			# Try to connect first
			if (not self.connected):
				self.connectToServer()

			# If connected, send the server a heartbeat message and update our gateway list
			if (self.connected): 
				self.sendHeartbeat()
				self.updateGateways()

			# Sleep it off man...
			print >> sys.stderr, "Resting..."
			time.sleep(int(self.paramMap["BRIDGE_SERVER_UPDATE_FREQ"]))

	def connectToServer(self):
		params = {'tmp' : 'tmp'}
		headers = {"Content-type": "application/json","Accept": "text/plain"}
		resp = self.sendMsg("POST", "/connect", params, headers)
		if (int(resp.status) == 200):
			self.connected = True

	def sendHeartbeat(self):
		params = {'tmp' : 'tmp'}
		headers = {"Content-type": "application/json","Accept": "text/plain"}
		return self.sendMsg("POST", "/heartbeat", params, headers)

	def sendMsg(self, cmd, url, params, headers):
		if (params == None or headers == None):
			self.conn.request(cmd, url)
		else:
			self.conn.request(cmd, url, json.dumps(params), headers)
		return conn.getresponse()

	def updateGateways(self):
		resp = self.sendMsg("GET", "/list-gateways", None, None)
		list = resp.read()
		print(list)
		dic = json.loads(list)
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
		# TODO
		raise RuntimeError()
