import psycopg
from .database_base import (
    DataBaseAbstract,
    DataBaseConfig,
    ErrorDBConnect,
    ErrorDBFetchError,
)
import os


class PostgresSQL(DataBaseAbstract):

    def __init__(self, connect_object: DataBaseConfig):
        super().__init__(connect_object=connect_object)
        self.connection_string: str = ""

    def decodeObject(self):
        self.connection_string = f"dbname='{self.connection_object.database}' user='{self.connection_object.username}' host='{self.connection_object.host}' password='{self.connection_object.password}' port='{self.connection_object.port}'"

    def new_connection(self):
        if len(self.connection_string) < 1:
            self.decodeObject()
        try:
            return psycopg.connect(self.connection_string)
        except Exception as e:
            raise ErrorDBConnect(
                message=f"Error DB Connect :{self.connection_object.database}"
            ) from e

    def execsql(self, connection, sql: str, params: list | dict = None) -> bool:
        # Returns True if the command was executed successfully
        # and False if it failed check SQL again
        try:
            in_cur = connection.cursor()
            in_cur.execute(sql, params)
            return True
        except Exception as e:
            print(e)
            raise ErrorDBFetchError(message="Error ExecSQL") from e

    def fetchone(self, connection, sql, params: list | dict = None) -> dict:
        try:
            in_cur = connection.cursor()
            in_cur.execute(sql, params)
            return in_cur.fetchone()
        except Exception as e:
            raise ErrorDBFetchError(message="Error FetchOne") from e

    def fetchall(self, connection, sql, params: list | dict = None) -> []:
        try:
            in_cur = connection.cursor()
            in_cur.execute(sql, params)
            return in_cur.fetchall()
        except Exception as e:
            raise ErrorDBFetchError(message="Error fetchAll") from e

    def commit(self, connection):
        connection.commit()

    def rollback(self, connection):
        connection.rollback()
