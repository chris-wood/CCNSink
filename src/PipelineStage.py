""" Abstract pipeline stage to enable modular and customizable message pipline.
"""
class PipelineStage(object):

	""" Create a pipeline stage with the specified name. Subclasses inheriting from this
	class will implement the thread run function and invoke it as needed.
	""" 
	def __init__(self, name):
		self.name = name
