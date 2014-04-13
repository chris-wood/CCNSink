class IncomingMessage(Message):

	def __init__(self, content, dstIp, dstPort, srcName):
		Message.__init__(self, content)
		self.srcIp = srcIp
		self.srcPort = srcPort
		self.srcName = srcName