import sys
import threading
import httplib
import time
import json
import asyncore
import socket
import os
import logging
from multiprocessing import Queue

socketMap = {}

# Setup logging redirection
logger = logging.getLogger('bridge')
hdlr = logging.FileHandler('./bridge.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

class BridgeHandler(asyncore.dispatcher_with_send):

	def setup(self, bridge, addr):
		self.started = False
		self.buffer = []
		self.bridge = bridge
		self.address = addr

		# Generate a random power and compute the DH half
		self.mod = bridge.mod
		self.gen = bridge.gen
		self.bits = bridge.bits
		rand = int(os.urandom(self.bits).encode('hex'), 16)
		self.power = (rand % (2 ** self.bits))
		self.ours = (self.gen ** self.power) % self.mod

		print >> sys.stderr, "Handler initialized"
		logger.info("Handler initialized")

	# self.request is the TCP socket connected to the client
	def handle_read(self):
		print >> sys.stderr, "inside handle_read"
		data = None
		if (not self.started):

			# retrieve key material
			length = self.recv(4)
			theirs = self.recv(length) # receive their DH half
			key = (self.ours ** int(theirs)) % self.mod
			self.bridge.keyMap[self.address] = key
			print >> sys.stderr, "established key: " + str(key)

			# retrieve interest
			length = self.recv(4)
			interest = self.recv(length) # receive their DH half
			print >> sys.stderr, "received interest = " + str(interest)
		if (data != None):
			self.send(data)

class BridgeServer(asyncore.dispatcher, threading.Thread):
	def __init__(self, bridge, host, port):
		asyncore.dispatcher.__init__(self)
		threading.Thread.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.addr = (host, port)
		self.listen(5) # this is the server queue size
		self.bridge = bridge

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			print >> sys.stderr, 'Incoming connection from %s' % repr(addr)
			logger.info('Incoming connection from %s' % repr(addr))
			handler = BridgeHandler(sock) # spins off a thread in the background
			handler.setup(self.bridge, addr)

	def run(self):
		print >> sys.stderr, "Starting BridgeServer on " + str(self.addr) + "\n"
		logger.info("Starting BridgeServer on " + str(self.addr))
		self.serve_forever()

	def serve_forever(self):
		asyncore.loop()

	def handle_close(self):
		self.close()

class Bridge(threading.Thread):
	def __init__(self, paramMap):
		threading.Thread.__init__(self)
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}
		self.socketMap = {}
		self.keyMap = {}
		self.connected = False
		self.server = BridgeServer(self, self.paramMap["PUBLIC_IP"], int(self.paramMap["BRIDGE_LOCAL_PORT"]))
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
		rand = int(os.urandom(self.bits).encode('hex'), 16)
		power = (rand % (2 ** self.bits))
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
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addrtuple = (targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"]))
			print >> sys.stderr, "Establishing socket connection to " + str(addrtuple)
			logger.info("Establishing socket connection to " + str(addrtuple))
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
		sock.send(str(interest))

	def retrieveContent(self, content, sourceAddress):
		raise RuntimeError()

if __name__ == "__main__":
	if (sys.argv[1] == "s"):
		server = BridgeServer(None, "192.168.1.10", 9000)
		server.start()
	else:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		addrtuple = ("192.168.1.10", 9000)
		print(addrtuple)
		sock.connect(addrtuple) # address is a tuple, e.g., targetAddress = ("www.python.org", 80)
		sock.send("hello world")