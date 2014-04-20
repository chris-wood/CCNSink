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
		if (self.ipTable.containsKey(tag)):
			tup = self.ipTable[tag]
			self.ipTable[tag] = (tup[0], tup[1], content)
			return True
		else:
			return False

	def updateNDNEntry(self, msg, content):
		if (self.ndnTable.containsKey(tag)):
			tup = self.ndnTable[tag]
			self.ndnTable[tag] = (tup[0], tup[1], content)
			return True
		else:
			return False

	def lookupIPEntry(self, tag):
		if (self.ipTable.containsKey(tag)):
			return self.ipTable[tag]
		else:
			return None

	def lookupNDNEntry(self, tag):
		if (self.ndnTable.containsKey(tag)):
			return self.ipTable[tag]
		else:
			return None

	def clearIPEntry(self, tag):
		if (self.ipTable.containsKey(tag)):
			del self.ipTable[tag]
			return True
		else:
			return False

	def clearNDNEntry(self, tag):
		if (self.ipTable.containsKey(tag)):
			del self.ndnTable[tag]
			return True
		else:
			return False

