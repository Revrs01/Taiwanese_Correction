import pymysql.cursors
from dotenv import load_dotenv
import os

load_dotenv()


class Cursor:
    def __init__(self):
        self.connection = pymysql.connect(host=os.getenv("DB_HOST"),
                                          user=os.getenv("DB_USER"),
                                          port=int(os.getenv("ALT_DB_PORT")),
                                          password=os.getenv("DB_PASSWORD"),
                                          database=os.getenv("DB_NAME"))

    def get_connection(self):
        return self.connection
