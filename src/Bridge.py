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
blockingMap = {}

def modExp(self, a, b, m):
	a %= m
	ret = None
	if b == 0:
		ret = 1
	elif b % 2:
		ret = a * modExp(a, b-1, m)
	else:
		ret = modExp(a, b//2, m)
		ret *= ret
	return (ret % m)

class BridgeHandler((SocketServer.BaseRequestHandler):

	def __init__(self, request, client_address, server):
		SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

	def setup(self):
		print >> sys.stderr, "Handler initialized for address: " + str(client_address)
		logger.info("Handler initialized")
        return SocketServer.BaseRequestHandler.setup(self)

	def handle(self):
		global bridgeServer
		global blockingMap
		length = int(self.request.recv(4))
		print >> sys.stderr, "received: " + str(length)
		data = self.request.recv(1024)
		print >> sys.stderr, "received: " + str(data)

		# Check to see if this is key data or an interest
		if (not (client_address in self.stage.keyMap)):	
			print >> "generating and returning key..."

			mod = bridgeServer.mod
			gen = bridgeServer.gen
			bits = bridgeServer.bits
			rand = random.randint(0, mod)
			power = (rand % (2 ** bits))
			ours = modExp(gen, power, mod)

			# Send our half back on down
			self.request.send(ours)
			
			# Compute and save our key
			theirs = int(data) # it was written as a string
			key = (ours ** int(theirs)) % mod
			self.stage.keyMap[client_address] = key
		else:
			print >> "forwarding interest..."
			interestName = data
			msg = OutgoingMessage(None, None, interestName, None, True)
			bridgeServer.ndnOutputStage.put(msg)
			return

	def finish(self):
		logger.info("BridgeHandler closing")
		return SocketServer.BaseRequestHandler.finish(self)

	# # self.request is the TCP socket connected to the client
	# def handle_read(self):
	# 	print >> sys.stderr, "inside handle_read"
	# 	data = None
	# 	if (not self.started):

	# 		# retrieve key material
	# 		length = self.recv(4)
	# 		theirs = self.recv(length) # receive their DH half
	# 		key = (self.ours ** int(theirs)) % self.mod
	# 		self.bridge.keyMap[self.address] = key
	# 		print >> sys.stderr, "established key: " + str(key)
	# 		logger.info("established key: " + str(key))

	# 		# retrieve interest
	# 		length = self.recv(4)
	# 		interest = self.recv(length) # receive their DH half
	# 		print >> sys.stderr, "received interest = " + str(interest)
	# 		logger.info("received interest = " + str(interest))

	# 	# Shove the data into the output buffer
	# 	if (data != None):
	# 		self.out_bfufer = data

class BridgeServer(SocketServer.TCPServer, threading.Thread):
	def __init__(self, host, port, handler_class = BridgeHandler):
		# asyncore.dispatcher.__init__(self)
		threading.Thread.__init__(self)
		# self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		# self.set_reuse_addr()
		# self.bind((host, port))
		# self.addr = (host, port)
		# self.listen(5) # this is the server queue size
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

	# def handle_accept(self):
	# 	pair = self.accept()
	# 	if pair is not None:
	# 		sock, addr = pair
	# 		print >> sys.stderr, 'Incoming connection from %s' % repr(addr)
	# 		logger.info('Incoming connection from %s' % repr(addr))
	# 		handler = BridgeHandler(sock) # spins off a thread in the background
	# 		handler.setup(self.bridge, addr)

	# def run(self):
	# 	print >> sys.stderr, "Starting BridgeServer on " + str(self.addr) + "\n"
	# 	logger.info("Starting BridgeServer on " + str(self.addr))
	# 	self.serve_forever()

	# def serve_forever(self):
	# 	asyncore.loop()

	# def handle_close(self):
	# 	self.close()

# class BridgeClient(asyncore.dispatcher_with_send):
# 	def __init__(self, host, port, data):
# 		asyncore.dispatcher.__init__(self)
# 		print >> sys.stderr, "Establishing socket connection to " + str(host)
# 		logger.info("Establishing socket connection to " + str(host))
# 		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
# 		self.connect((host, port))
# 		self.receiveBuffer = []
# 		self.out_buffer = str(data)

# 	# def send_data(self, data):
# 	# 	print >> sys.stderr, "Sending: " + str(data)
# 	# 	self.out_buffer = data

# 	def handle_close(self):
# 		self.close()

# 	def handle_read(self):
# 		length = self.recv(4)
# 		self.receiveBuffer.append(length)
# 		data = str(self.recv(length))
# 		self.receiveBuffer.append(data)
# 		print >> sys.stderr, "Received: "  + str(data)
# 		self.close()

class Bridge(threading.Thread):
	def __init__(self, paramMap, ndnOutputStage):
		threading.Thread.__init__(self)
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
		bridgeServer = BridgeServer(self.paramMap["PUBLIC_IP"], int(self.paramMap["BRIDGE_LOCAL_PORT"]))

	def run(self):
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

	# Generate our half of the DH share
	def generatePairwiseKey(self, sock):
		# rand = int(os.urandom(self.bits).encode('hex'), 16)
		rand = random.randint(0, self.mod)
		power = (rand % (2 ** self.bits))
		# ours = (self.gen ** power) % self.mod
		ours = modExp(self.gen, power, self.mod)
		return ours

		# Send our half of the share to the other guy
		sharestr = str(ours)
		print >> sys.stderr, "sending data..."
		sock.send_data(len(sharestr))
		sock.send_data(sharestr)

		# Receive their share
		print >> sys.stderr, "receving data...."
		length = int(sock.recv(4))
		theirs = sock.recv(length)

		# Compute and save the key
		key = (ours ** int(theirs)) % mod
		return key

	# Messages are sent as follows: |name length|name|
	def sendInterest(self, interest, targetAddress):
		print("sending interest")
		global blockingMap
		if (targetAddress != self.paramMap["PUBLIC_IP"]): # don't forward to ourselves..
			sock = None

			# Retrieve socket
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"])))

			print >> sys.stderr, "Socket retrieved - sending data"
			logger.info("Socket retrieved - sending data")

			# Check to see if we need to establish a key
			if (not (targetAddress in self.keyMap)):
				key = self.generatePairwiseKey(sock)
				self.keyMap[targetAddress] = key
				print >> sys.stderr, "New key establsihed"
				logger.info("New key established")

				# Refresh the socket
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((targetAddress, int(self.paramMap["BRIDGE_LOCAL_PORT"])))
			
			# Send the interest now
			sock.send(len(interest))
			sock.send(interest)

			semaphore = multiprocessing.BoundedSemaphore(0)
			blockingMap[str(interest)] = semaphore # save reference for later on down the road

			return CONTENT HERE
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