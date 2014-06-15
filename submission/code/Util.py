''' File with some shared (and useful) utility functions.
    Basically, this is where the crypto wrappers go.
'''

import hmac

def generateHMACTag(key, content):
	digester = hmac.new(str(key))
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

def iterModExp(a, b, m):
	r = 1
	while 1:
		if b % 2 == 1:
			r = (r * a) % m
		b /= 2
		if b == 0:
			break
		a = (a * a) % m
	return r
