class Message(object):

	def __init__(self, content, tag, protocol):
		self.content = content
		self.tag = str(tag)
		self.protocol = str(protocol)