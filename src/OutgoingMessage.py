from Message import *

class OutgoingMessage(Message):

	def __init__(self, srcInfo, dstInfo, dstName):
		Message.__init__(self, dstName, dstName) # the destination name is the same as the tag in this case
		self.srcInfo = srcInfo
		self.dstInfo = dstInfo
		self.dstName = dstName
		