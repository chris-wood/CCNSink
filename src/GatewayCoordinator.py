from FlaskBackend import *

DATABASE = './db/coordinator.db'

# Open up a DB connection before the request
@app.before_request
def before_request():
	g.db = connect_db()

# Close it after
@app.after_request
def after_request(response):
	g.db.close()
	return response

# Return the status of the directory
@app.route("/status")
def req_status():
    return "TODO"

# Add the requesting gateway to the directory
@app.route("/connect")
def req_connect():
	return "TODO"

# Return a JSON-formatted list of all gateway addresses
@app.route("/list-gateways")
def req_list_gateways():
	str = ""
	for gateway in query_db('select * from gateways'):
    	str = str + gateway['address'], 'has the id', gateway['gateway_id']
	return str
