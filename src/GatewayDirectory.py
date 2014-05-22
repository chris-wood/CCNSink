# Flask web app server imports
from flask import Flask
app = Flask(__name__)

# Database imports
import sqlite3
from flask import g

################################################
################ DATABASE CODE #################
################################################

# Database connection establishment helper
DATABASE = './db/directory.db'
def connect_db():
	return sqlite3.connect(DATABASE)

# Open up a DB connection before the request
@app.before_request
def before_request():
	g.db = connect_db()

# Close it after
@app.after_request
def after_request(response):
	g.db.close()
	return response

# Helper function for the database
def query_db(query, args=(), one=False):
	cur = g.db.execute(query, args)
	rv = [dict((cur.description[idx][0], value)
		for idx, value in enumerate(row)) for row in cur.fetchall()]
	return (rv[0] if rv else None) if one else rv

################################################
########### DIRECTORY API BELOW ################
################################################

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
