from SqlCursor import Cursor

SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()
