import sys
import threading
import httplib
import time
import json
import asyncore
import socket
import os
import logging
import random
import multiprocessing
import SocketServer
from OutgoingMessage import *
from Util import *
from multiprocessing import Queue

# Setup logging redirection
logger = logging.getLogger('bridge')
hdlr = logging.FileHandler('./bridge.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

# Global ref to the singleton bridge server running on this node
bridgeServer = None
FIT = {} # map from interest name to (semaphore, content) tuples (this blocks the exit bridge)
PIT = {} # map from interest name to (semaphore, content) tuples (this blocks the entry bridge)

class BridgeHandler(SocketServer.BaseRequestHandler):

	def __init__(self, request, client_address, server):
		self.client_address = client_address
		self.server = server
		SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

	def setup(self):
		print >> sys.stderr, "Handler initialized for address: " + str(self.client_address)
		logger.info("Handler initialized")
		return SocketServer.BaseRequestHandler.setup(self)

	def handle(self):
		global bridgeServer
		lengths = []
		dtype = self.request.recv(1)
		if (dtype == 'k'):
			print >> sys.stderr, "received generating and returning key..."

			fin = self.request.makefile()
			bytes = ""
			byte = fin.read(1)
			while (byte != "\n"):
				bytes = bytes + byte
				byte = fin.read(1)
			data = bytes

			mod = bridgeServer.mod
			gen = bridgeServer.gen
			bits = bridgeServer.bits
			rand = random.randint(0, mod)
			power = (rand % (2 ** bits))
			ours = modExp(gen, power, mod)

			# Send our half back on down
			fout = self.request.makefile()
			returnData = str(ours) + "\n"
			fout.write(returnData)
			fout.flush()
			
			# Compute and save our key
			theirs = int(data) # it was written as a string
			key = modExp(ours, int(theirs), mod)
			bridgeServer.stage.keyMap[self.client_address[0]] = key
			
			return
		elif (dtype == 'i'):
			print >> sys.stderr, "received, forwarding interest..."
		
			fin = self.request.makefile()
			bytes = ""
			byte = fin.read(1)
			while (byte != "\n"):
				bytes = bytes + byte
				byte = fin.read(1)
			interestName = bytes

			msg = OutgoingMessage(None, None, interestName, None, True)
			event = threading.Event()

			# Send the interest now and block
			bridgeServer.stage.ndnOutputStage.put(msg, event)
			event.clear()
			event.wait()

			# We've returned - fetch the content
			content = str(bridgeServer.stage.ndnOutputStage.bridgeFIT[msg.tag][1])

			# Sign the content using the key for the bridge
			if (bridgeServer.stage.keyMap[self.client_address[0]] != None):
				sig = generateHMACTag(bridgeServer.stage.keyMap[self.client_address[0]], content)

				# Send the content and the signature to the other bridge
				fout = self.request.makefile()
				fout.write(content + "\n")
				fout.write(sig + "\n")
				fout.flush()
			else:
				raise RuntimeError()

			return

	def finish(self):
		logger.info("BridgeHandler closing")
		return SocketServer.BaseRequestHandler.finish(self)

class BridgeServer(SocketServer.TCPServer, threading.Thread):
	def __init__(self, host, port, mod, gen, bits, stage, handler_class = BridgeHandler):
		threading.Thread.__init__(self)
		self.gen = gen
		self.mod = mod
		self.bits = bits
		self.stage = stage
		SocketServer.TCPServer.__init__(self, (host, port), handler_class)

	def server_activate(self):
		SocketServer.TCPServer.server_activate(self)
		return

	def run(self):
		self.running = True
		while (self.running):
			self.handle_request()
		return

	def handle_request(self):
		print >> sys.stderr, "BridgeServer handle_request"
		return SocketServer.TCPServer.handle_request(self)

	def verify_request(self, request, client_address):
		return SocketServer.TCPServer.verify_request(self, request, client_address)

	def process_request(self, request, client_address):
		return SocketServer.TCPServer.process_request(self, request, client_address)

	def server_close(self):
		return SocketServer.TCPServer.server_close(self)

	def finish_request(self, request, client_address):
		return SocketServer.TCPServer.finish_request(self, request, client_address)

	def close_request(self, request_address):
		return SocketServer.TCPServer.close_request(self, request_address)

class Bridge(threading.Thread):
	def __init__(self, paramMap, ndnOutputStage):
		threading.Thread.__init__(self)
		global bridgeServer
		self.paramMap = paramMap
		self.gateways = []
		self.prefixGatewayMap = {}
		self.keyMap = {}
		self.connected = False
		self.ndnOutputStage = ndnOutputStage
		self.mod = int(self.paramMap["KEYGEN_GROUP_MODULUS"])
		self.gen = int(self.paramMap["KEYGEN_GROUP_GENERATOR"])
		self.bits = int(self.paramMap["KEYGEN_KEY_BITS"])

		# Create the global server 
		bridgeServer = BridgeServer(self.paramMap["PUBLIC_IP"], int(self.paramMap["BRIDGE_LOCAL_PORT"]), self.mod, self.gen, self.bits, self)

	def run(self):
		global bridgeServer
		self.running = True
		bridgeServer.start()

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

	# Generate our half of the DH share
	def generatePairwiseKey(self, sock):
		rand = random.randint(0, self.mod)
		power = (rand % (2 ** self.bits))
		ours = modExp(self.gen, power, self.mod)

		# Send our half of the share to the other guy
		sharestr = str(ours)
		payload = "k" + sharestr + "\n"
		fout = sock.makefile()
		fout.write(payload)
		fout.flush()

		# Receive their share
		fin = sock.makefile()
		bytes = ""
		byte = fin.read(1)
		while (byte != "\n"):
			bytes = bytes + byte
			byte = fin.read(1)
		theirs = int(bytes)


		# Compute and save the key
		key = modExp(ours, theirs, self.mod)
		return key

	# Messages are sent as follows: |name length|name|
	def sendInterest(self, interest, targetAddress):
		global PIT

		interest = str(interest)

		if (targetAddress != self.paramMap["PUBLIC_IP"]): # don't forward to ourselves..
			sock = None

			# Retrieve socket
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"])))
			# fout = sock.makefile()

			print >> sys.stderr, "Socket retrieved - sending data"
			logger.info("Socket retrieved - sending data")

			# Check to see if we need to establish a key
			if (not (targetAddress in self.keyMap)):
				keyStart = time.time()
				key = self.generatePairwiseKey(sock)
				self.keyMap[targetAddress] = key
				keyEnd = time.time()
				diff = end - keyStart
				logger.info('BRIDGE-KEY-EST: ' + str(diff))
				print >> sys.stderr, "New key establsihed: " + str(key)
				logger.info("New key established: " + str(key))

				# Refresh the socket
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"])))

			# Send the interest now
			payload = "i" + interest + "\n"
			fout = sock.makefile()
			fout.write(payload)
			fout.flush()

			# Block and wait for the content and then its signature
			fin = sock.makefile()
			bytes = ""
			byte = fin.read(1)
			while (byte != "\n"):
				bytes = bytes + byte
				byte = fin.read(1)
			content = str(bytes)

			# Signature
			byte = fin.read(1)
			bytes = ""
			while (byte != "\n"):
				bytes = bytes + byte
				byte = fin.read(1)
			sig = str(bytes)

			# Verify the signature (tag)
			tag = generateHMACTag(self.keyMap[targetAddress], content)
			if (tag != sig):
				print >> sys.stderr, "MAC tag verification failed (exp, got): " + str(tag) + ", " + str(sig)
				return None
			else:
				return content
		else:
			return None

	def returnContent(self, content, sourceAddress):
		raise RuntimeError()

# Runnable unit for testing...
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