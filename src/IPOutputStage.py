from PipelineStage import *

stage = None

class IPOutputStage(PipelineStage):
	def __init__(self, name, nextStage = None, table = None, paramMap = {}):
		global stage
		self.name = name
		self.nextStage = nextStage
		self.table = table
		stage = self # set the reference so the handler can refer back to this stage

