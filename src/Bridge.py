import sys
import threading
import httplib
import time
import json
import asyncore
import socket
import os
from multiprocessing import Queue

socketMap = {}

class BridgeHandler(asyncore.dispatcher_with_send, threading.Thread):
	def __init__(self, bridge, sock, addr):
		threading.Thread.__init__(self)
		self.started = False
		self.buffer = []
		self.bridge = bridge

		# Generate a random power and compute the DH half
		self.power = (os.urandom(bridge.bits) % (2 ** bridge.bits))
		self.ours = (bridge.gen ** power) % bridge.mod		

		# TODO: use address
		self.address = addr

	# self.request is the TCP socket connected to the client
	def handle_read(self):
		data = None
		if (not self.started):
			length = self.recv(4)
			theirs = self.recv(length) # receive their DH half
			key = (self.ours ** int(theirs)) % self.mod
			bridge.keyMap[self.address] = key
		if (data != None):
			self.send(data)

class BridgeServer(asyncore.dispatcher, threading.Thread):
	def __init__(self, bridge, host, port):
		asyncore.dispatcher.__init__(self)
		threading.Thread.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.listen(5)
		self.bridge = bridge

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			print >> sys.stderr, 'Incoming connection from %s' % repr(addr)
			handler = BridgeHandler(bridge, sock, addr) # spins off a thread in the background

	def run(self):
		asyncore.loop()

class Bridge(threading.Thread):
	def __init__(self, paramMap):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}
		self.socketMap = {}
		self.keyMap = {}
		self.connected = False
		self.server = BridgeServer(self, self.paramMap["LOCALHOST"], self.paramMap["BRIDGE_LOCAL_PORT"])
		self.mod = int(self.paramMap["KEYGEN_GROUP_MODULUS"])
		self.gen = int(self.paramMap["KEYGEN_GROUP_GENERATOR"])
		self.bits = int(self.paramMap["KEYGEN_KEY_BITS"])

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
		return self.conn.getresponse()

	def updateGateways(self):
		resp = self.sendMsg("GET", "/list-gateways", None, None)
		list = resp.read()
		print(list)
		dic = json.loads(list)
		self.gateways = []
		for gateway in dic["gateways"]:
			self.gateways.append(str(gateway)) # gateway should be the address

	def getGateways(self):
		return self.gateways

	def lookupPrefix(self, prefix):
		if (prefix in self.prefixGatewayMap):
			return self.prefixGatewayMap[prefix]
		else:
			return None

	def establishPairwiseKey(self, targetAddress, sock):
		# Generate our half of the DH share
		power = (os.urandom(self.bits) % (2 ** self.bits))
		ours = (self.gen ** power) % self.mod

		# Send our half of the share to the other guy
		sharestr = str(ours)
		sock.send(len(sharestr))
		sock.send(sharestr)

		# Receive their share
		length = sock.recv(4)
		theirs = sock.recv(length)

		# Compute and save the key
		key = (ours ** int(theirs)) % mod
		self.keyMap[targetAddress] = key

	# Messages are sent as follows: |name length|name|
	def sendInterest(self, interest, targetAddress):
		sock = None

		# Retrieve socket
		if (not (targetAddress in self.socketMap)):
			print("TODO: establish a socket connection to the address")
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addrtuple = (targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"]))
			sock.connect(addrtuple) # address is a tuple, e.g., targetAddress = ("www.python.org", 80)
			self.socketMap[targetAddress] = sock
		else:
			sock = self.socketMap[targetAddress]

		# Check to see if we have a shared key pair before sending an interest
		# This occurs when we have not previously established a connection to the target
		if (not (targetAddress in self.keyMap)):
			self.establishPairwiseKey(targetAddress, sock)
		
		# With a working socket and shared key, send the message
		nameLen = len(interest)
		sock.send(nameLen)
		sock.send(interest)

	def retrieveContent(self, content, sourceAddress):
		# TODO
		raise RuntimeError()
