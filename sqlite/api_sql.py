from .sql import SqlEngine

class ApiTable(SqlEngine):
    def __init__(self):
        super().__init__()
    def create_api_table(self):
        sql_structure = """
        CREATE TABLE IF NOT EXISTS api_table (
            id INTEGER PRIMARY KEY,
            api_name TEXT UNIQUE,
            api_key TEXT)
        """
        self.cursor.execute(sql_structure)
    
    def insert_api_data(self, api_name, api_key):
        sql_insert = """
        INSERT INTO api_table (api_name, api_key) VALUES (?, ?)
        """
        self.cursor.execute(sql_insert, (api_name, api_key))
        self.conn.commit()
    
    def get_api_data(self, api_name):
        sql_select = """
        SELECT * FROM api_table WHERE api_name = ?
        """
        self.cursor.execute(sql_select, (api_name,))
        return self.cursor.fetchone()

    def update_api_data(self, api_name, api_key):
        sql_update = """
        UPDATE api_table SET api_key = ? WHERE api_name = ?
        """
        self.cursor.execute(sql_update, (api_key, api_name))
        self.conn.commit()
    
    def del_api_data(self, api_name):
        sql_del = """
        DELETE FROM api_table WHERE api_name = ?
        """
        self.cursor.execute(sql_del, (api_name,))
        self.conn.commit()