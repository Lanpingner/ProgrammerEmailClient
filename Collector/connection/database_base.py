from abc import ABC, abstractmethod
from .exception_handler import LeviathanError


class ErrorDBCollect(LeviathanError):
    pass


class ErrorDBConnect(LeviathanError):
    pass


class ErrorDBFetchError(LeviathanError):
    pass


class ErrorRemoteIdMissing(LeviathanError):
    pass


class DataBaseConfig:
    """Property class for DataBase instances

    Returns:
        _type_: _description_
    """

    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""

    def __init__(self):
        return

    def __repr__(self):
        return str(
            {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "username": self.username,
                "password": self.password,
            }
        )


class DataBaseAbstract(ABC):
    connection_object: DataBaseConfig = None

    def __init__(self, connect_object: DataBaseConfig):
        self.connection_object = connect_object

    @abstractmethod
    def execsql(self, connection, sql: str, params: list | dict = None):
        pass

    @abstractmethod
    def fetchall(self, connection, sql: str, params: list | dict = None):
        pass

    @abstractmethod
    def fetchone(self, connection, sql: str, params: list | dict = None):
        pass

    @abstractmethod
    def new_connection(self):
        pass

    @abstractmethod
    def commit(self, connection):
        pass
