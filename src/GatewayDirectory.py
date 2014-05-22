from FlaskBackend import *

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
		print(e)
		abort(500) 

# Handle heartbeat
@app.route("/heartbeat", methods = ['GET'])
def get_heartbeat():
	abort(400)
@app.route("/heartbeat", methods = ['POST'])
def post_heartbeat():
	assert request.path == '/heartbeat'
	assert request.method == 'POST'
	print("post_heartbeat")
	# print(str(request.form['fieldname']))
	# TODO

# Add the requesting gateway to the directory
@app.route("/connect", methods = ['GET'])
def get_connect():
	abort(400)
@app.route("/connect", methods = ['POST'])
def post_connect():
	assert request.path == '/connect'
	assert request.method == 'POST'
	print("post_connect")
	# TODO

# Return a JSON-formatted list of all gateway addresses
@app.route("/list-gateways", methods = ['GET'])
def get_list_gateways():
	str = ""
	for gateway in query_db('select * from gateways'):
		print gateway['address'], 'has the id', gateway['gateway_id']
	return str

if __name__ == "__main__":
    app.run()