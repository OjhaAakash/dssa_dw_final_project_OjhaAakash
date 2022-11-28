import psycopg
from psycopg import connect, connection, cursor

conn = psycopg.connect(
    host = "localhost",
    user = "postgres",
    port =  5432,
    password = "aakashojha873Qa")

cursor = cursor(name=None, cursor_factory=None, scrollable=None, withhold=False)
cursor.close()
cursor