import sys
import threading
import time
import yaml # for config file parsing
from Prompt import *
from IPOutputStage import *
from IPInputStage import *

""" Main class that orchestrates the behavior and operation of the gateway, including all
internal pipeline components.
"""
class NDNGateway(threading.Thread):

	""" Construct the gateway using parameters from the paramMap.
	"""
	def __init__(self, sleepTime = 2, paramMap = {}):
		threading.Thread.__init__(self)
		self.sleepTime = sleepTime

		# IP input pipeline
		ipOutput = IPOutputStage("IPOutputStage", None)
		ipInput = IPInputStage("IPInputStage", None, paramMap)
		ipInput.start()

		# IP output pipeline
		#TODO

		# NDN input pipeline
		#TODO

		# NDN output pipeline
		#TODO

	def run(self):
		self.running = True
		while (self.running):
			time.sleep(self.sleepTime)

		# Print closing remarks
		print("?> NDNGateway terminating...")

	def stop(self):
		self.running = False


""" Main entry point for the gateway.
"""
def main():
	# Parse cmd line arguments
	if len(sys.argv) != 2:
		print >> sys.stderr, "Usage: python NDNGateway.py <config_file>"
		return

	# Parse the config file
	cfgFile = open(sys.argv[1], 'r')
	paramMap = yaml.load(cfgFile)
	print(paramMap)

	# Create the gateway
	gateway = NDNGateway(paramMap = paramMap)
	gateway.start()

	#### TODO: wait for initialization

	# Start command prompt to handle all runtime user input
	prompt = Prompt(gateway)
	prompt.start()

	# Print closing remarks
	gateway.join()
	prompt.join()
	print("Goodbye!")

if __name__ == "__main__":
	main()