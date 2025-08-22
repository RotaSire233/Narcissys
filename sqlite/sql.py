import sqlite3
import os

class SqlEngine:
    def __init__(self, sqlite_file_path='datas/sql.db'):
        self.root_path = os.path.dirname(os.path.abspath(__file__))
        self.sqlite_file_path = os.path.join(self.root_path, sqlite_file_path)
        self.conn = sqlite3.connect(self.sqlite_file_path)
        self.cursor = self.conn.cursor()
    def close_sql(self):
        self.conn.close()
    


    

    