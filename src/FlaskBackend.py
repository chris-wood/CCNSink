# Flask web app server imports
from flask import Flask, jsonify, abort, request
app = Flask(__name__)

# Database imports
import sqlite3
from flask import g

# Database connection establishment helper
def connect_db(database):
	return sqlite3.connect(database)

# Helper function for the database
def query_db(query, args=(), one=False):
	cur = g.db.execute(query, args)
	rv = [dict((cur.description[idx][0], value)
		for idx, value in enumerate(row)) for row in cur.fetchall()]
	return (rv[0] if rv else None) if one else rv
