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
def req_status():
	try:
		resp = jsonify({'status' : 'ONLINE'})
		return resp
	except Exception as e:
		print(e)
		abort(500) 


# Add the requesting gateway to the directory
@app.route("/connect", methods = ['PUT'])
def req_connect():
	return "TODO"

# Return a JSON-formatted list of all gateway addresses
@app.route("/list-gateways", methods = ['GET'])
def req_list_gateways():
	str = ""
	for gateway in query_db('select * from gateways'):
		print gateway['address'], 'has the id', gateway['gateway_id']
	return str

if __name__ == "__main__":
    app.run()