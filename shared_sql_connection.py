from SqlCursor import Cursor

SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()

def reconnect():
    global SQL_CONNECTION, SQL_CURSOR
    SQL_CONNECTION.ping()
    SQL_CURSOR = SQL_CONNECTION.cursor()
