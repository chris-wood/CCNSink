from Message import *

class PendingMessageTable(object):
	def __init__(self):
		self.ipTable = {}
		self.ndnTable = {}

	def insertIPEntry(self, msg, lock):
		self.ipTable[msg.tag] = (msg, lock, None)

	def insertNDNEntry(self, msg, lock):
		self.ndnTable[msg.tag] = (msg, lock, None)

	def updateIPEntry(self, tag, content):
		if (tag in self.ipTable):
			tup = self.ipTable[tag]
			self.ipTable[tag] = (tup[0], tup[1], content)
			return True
		else:
			return False

	def updateNDNEntry(self, tag, content):
		if (tag in self.ndnTable):
			tup = self.ndnTable[tag]
			self.ndnTable[tag] = (tup[0], tup[1], content)
			return True
		else:
			return False

	def lookupIPEntry(self, tag):
		if (tag in self.ipTable):
			return self.ipTable[tag]
		else:
			return None

	def lookupNDNEntry(self, tag):
		if (tag in self.ndnTable):
			return self.ndnTable[tag]
		else:
			return None

	def clearIPEntry(self, tag):
		if (tag in self.ipTable):
			del self.ipTable[tag]
			return True
		else:
			return False

	def clearNDNEntry(self, tag):
		if (tag in self.ndnTable):
			del self.ndnTable[tag]
			return True
		else:
			return False

