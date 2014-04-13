import sys
import threading
import time
from Prompt import *

""" Main class that orchestrates the behavior and operation of the gateway, including all
internal pipeline components.
"""
class NDNGateway(threading.Thread):

	""" Construct the gateway using parameters from the paramMap.
	"""
	def __init__(self, sleepTime = 2, paramMap = {}):
		threading.Thread.__init__(self)
		self.sleepTime = sleepTime

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
	# Create the gateway
	gateway = NDNGateway()
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