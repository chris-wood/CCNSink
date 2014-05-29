from FlaskBackend import *
import sys
import json
import datetime

app.debug = True

DATABASE = './db/directory.db'

# Open up a DB connection before the request
@app.before_request
def before_request():
	g.db = connect_db(DATABASE)

# Close it after
@app.after_request
def after_request(response):
	g.db.close()
	return response

# Return the status of the directory
@app.route("/status", methods = ['GET'])
def get_status():
	try:
		resp = jsonify({'status' : 'ONLINE'})
		return resp
	except Exception as e:
		print >> sys.stderr, str(e)
		abort(500) 

# Handle heartbeat
@app.route("/heartbeat", methods = ['GET'])
def get_heartbeat():
	abort(400)
@app.route("/heartbeat", methods = ['POST'])
def post_heartbeat():	
	assert request.path == '/heartbeat'
	assert request.method == 'POST'
	assert request.headers['Content-Type'] == 'application/json'
	print >> sys.stderr, "DEBUG: post_heartbeat"
	try:	
		data = json.loads(request.data)
		addr = request.remote_addr
		match = query_db('select * from gateways where address = "' + str(addr) + '";')
		if (match != None and len(match) > 0):
			gid = str(match['gateway_id'])
			query_db('update gateways set address = "' + str(addr) + '" where gateway_id = ' + gid + ';')
		else:
			print >> sys.stderr, "Received heartbeat from invalid gateway at " + str(addr)
		return jsonify(result = {"status" : 200})
	except Exception as e: 
		print >> sys.stderr, str(e)
		abort(500)

# Add the requesting gateway to the directory
@app.route("/connect", methods = ['GET'])
def get_connect():
	abort(400)
@app.route("/connect", methods = ['POST'])
def post_connect():
	assert request.path == '/connect'
	assert request.method == 'POST'
	assert request.headers['Content-Type'] == 'application/json'
	print >> sys.stderr, "DEBUG: post_connect"
	try:
		data = json.loads(request.data)
		addr = request.remote_addr

		# Insert the address into the database - don't overwrite if already there
		match = query_db('select * from gateways where address = "' + str(addr) + '";')
		if (match == None):
			query_db('insert into gateways(address, last_update) values ("' + str(addr) + '", "' + str(datetime.datetime.now()) + '");')
		else: # update the last_update time
			print(match)
			time = str(datetime.datetime.now())
			gid = str(match['gateway_id'])
			query_db('update gateways set last_update = "' + time + '" where gateway_id = ' + gid + ';')
		
		# TOOD: authenticate the client
		# cert = data["certificate"]

		return jsonify(result = {"status" : 200})
	except Exception as e:
		print >> sys.stderr, str(e)
		abort(500)

# Return a JSON-formatted list of all gateway addresses
@app.route("/list-gateways", methods = ['GET'])
def get_list_gateways():
	addresses = []
	try:
		for gateway in query_db('select * from gateways;'):
			addresses.append(gateway['address'])
			print gateway['address'], 'has the id', gateway['gateway_id']
		list = {'gateways' : addresses}
		print(addresses)
		print(list)
		return jsonify(list)
	except Exception as e:
		print >> sys.stderr, str(e)
		abort(500)

if __name__ == "__main__":
    app.run(host='0.0.0.0')