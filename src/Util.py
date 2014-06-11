''' File with some shared (and useful) utility functions.
'''

import hmac

def generateHMACTag(key, content):
	digester = hmac.new(key)
	digester.update(content)
	return digester.hexdigest()

def modExp(a, b, m):
	a %= m
	ret = None
	if b == 0:
		ret = 1
	elif b % 2:
		ret = a * modExp(a, b-1, m)
	else:
		ret = modExp(a, b//2, m)
		ret *= ret
	return (ret % m)

