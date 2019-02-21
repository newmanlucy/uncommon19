import sqlite3

def create_db():
	conn = sqlite3.connect("weather_betting.db")
	c = conn.cursor()
	c.execute("""
		CREATE TABLE users (username TEXT PRIMARY KEY)
	""")
	c.execute("""
		CREATE TABLE bets (
			id INTEGER PRIMARY KEY,
			atleast INTEGER,
			date DATE,
			amount INTEGER,
			creator_id TEXT,
			taker_id TEXT,
			FOREIGN KEY (taker_id) REFERENCES users,
			FOREIGN KEY (creator_id) REFERENCES users
		)
	""")
	conn.commit()
	conn.close()

if __name__ == '__main__':
	create_db()