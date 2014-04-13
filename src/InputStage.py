import threading
import time

class InputStage(PipelineStage):

	def __init__(self, name):
		PipelineStage.__init__(name)
		threading.Thread.__init__(self)

	def run(self):
		print "Starting " + self.name

