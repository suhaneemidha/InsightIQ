import duckdb

con = duckdb.connect("olist.db")

print(con.execute("SHOW TABLES").fetchall())

con.close()