from PipelineStage import *

class IPOutputStage(PipelineStage):
	def __init__(self, name, nextStage = None, table, paramMap = {}):
		self.name = name
		self.nextStage = nextStage
		self.table = table
		stage = self # set the reference so the handler can refer back to this stage