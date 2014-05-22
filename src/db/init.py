# Database imports
import sqlite3
from flask import Flask
app = Flask(__name__)

DATABASE = './directory.db'
SCHEMA = './directory_schema.sql'

def connect_db():
	return sqlite3.connect(DATABASE)

# Database schema initialization code
from contextlib import closing
def init_db():
	with closing(connect_db()) as db:
		with app.open_resource(SCHEMA) as f:
			db.cursor().executescript(f.read())
		db.commit()

if __name__ == "__main__":
	init_db()