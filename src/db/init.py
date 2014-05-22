# Database imports
import sqlite3
from flask import Flask
app = Flask(__name__)

GATEWAY_DB = './directory.db'
GATEWAY_SCHEMA = './directory_schema.sql'
COORDINATOR_DB = './coordinator.db'
COORDINATOR_SCHEMA = './coordinator_schema.sql'

def connect_db(database):
	return sqlite3.connect(database)

# Database schema initialization code
from contextlib import closing
def init_db(database, schema):
	with closing(connect_db()) as db:
		with app.open_resource(schema) as f:
			db.cursor().executescript(f.read())
		db.commit()

if __name__ == "__main__":
	init_db(GATEWAY_DB, GATEWAY_SCHEMA)
	# init_db(COORDINATOR_DB, COORDINATOR_SCHEMA)


