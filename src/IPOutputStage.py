from PipelineStage import *

class IPOutputStage(PipelineStage):
	def __init__(self, name, nextStage = None, paramMap = {}):
		self.name = name
		self.nextStage = nextStage
		stage = self # set the reference so the handler can refer back to this stage