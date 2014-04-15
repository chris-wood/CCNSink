from PipelineStage import *

class NDNOutputStage(PipelineStage):
	def __init__(self, name, nextStage = None, paramMap = {}):
		self.name = name
		self.nextStage = nextStage