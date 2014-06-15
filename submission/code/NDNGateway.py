import sys
import threading
import time
import yaml 
from GatewayPrompt import *
from IPOutputStage import *
from IPInputStage import *
from NDNOutputStage import *
from NDNInputStage import *
from PendingMessageTable import *

""" Main class that orchestrates the behavior and operation of the gateway, including all
internal pipeline components.
"""
class NDNGateway(threading.Thread):

	""" Construct the gateway using parameters from the paramMap.
	"""
	def __init__(self, sleepTime = 2, paramMap = {}):
		threading.Thread.__init__(self)
		self.sleepTime = sleepTime
		self.stages = []

		# Shared pending message table
		table = PendingMessageTable()

		# Create output stages
		ndnOutput = NDNOutputStage("NDNOutputStage", table, paramMap) # there is no next stage after output
		self.stages.append(ndnOutput)
		ndnOutput.start()
		ipOutput = IPOutputStage("IPOutputStage", table, paramMap) # there is no next stage after output
		self.stages.append(ipOutput)

		# IP input pipeline and connect it to the output stage
		ipInput = IPInputStage("IPInputStage", ndnOutput, table, paramMap)
		self.stages.append(ipInput)
		ipInput.start()
		ndnInput = NDNInputStage("NDNInputStage", ipOutput, ndnOutput, table, paramMap)
		self.stages.append(ndnInput)
		ndnInput.start()

	def run(self):
		self.running = True
		while (self.running):
			time.sleep(self.sleepTime)

		# Print closing remarks
		print("?> NDNGateway terminating...")
		for s in self.stages:
			s.stop()

	def stop(self):
		self.running = False


""" Main entry point for the gateway.
"""
def main():
	# Parse cmd line arguments
	if len(sys.argv) != 3:
		print >> sys.stderr, "Usage: python NDNGateway.py <config_file> <ipaddress>"
		return

	# Parse the config file
	cfgFile = open(sys.argv[1], 'r')
	paramMap = yaml.load(cfgFile)
	print(paramMap)

	# Retrieve IP address
	ip = sys.argv[2]
	paramMap["PUBLIC_IP"] = ip

	# Create the gateway
	gateway = NDNGateway(paramMap = paramMap)
	gateway.start()

	# Start command prompt to handle all runtime user input
	prompt = GatewayPrompt(gateway)
	prompt.start()

	# Print closing remarks
	gateway.join()
	prompt.join()
	print("Goodbye!")

if __name__ == "__main__":
	main()

