class OutgoingMessage(Message):

	def __init__(self, content, dstIp, dstPort, dstName):
		Message.__init__(self, content)
		self.dstIp = dstIp
		self.dstPort = dstPort
		self.dstName = dstName