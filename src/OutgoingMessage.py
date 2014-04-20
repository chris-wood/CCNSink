from Message import *

class OutgoingMessage(Message):

	def __init__(self, srcInfo, dstInfo, dstName):
		Message.__init__(self, dstName)
		self.srcInfo = srcInfo
		self.dstInfo = dstInfo
		self.dstName = dstName
		