import sqlite3
conn = sqlite3.connect('instance/finanzas.db')
print(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
