# config/db_config.py
import pyodbc

class DBconnection:

    @staticmethod
    def get_connection():
        try:
            conn_str = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=localhost\\SQLEXPRESS;" 
                "DATABASE=Cho_online;"
                "UID=sa;"
                "PWD=123"
            )
            return pyodbc.connect(conn_str)
        except pyodbc.Error as e:
            print("Lỗi kết nối Database gốc:", e)
            return None