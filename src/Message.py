class Message(object):

	def __init__(self, content, direction = 0):
		self.content = content
		self.direction = direction # direction of the message, 0 = inbound, 1 = outbound