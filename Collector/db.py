from connection.postgres_connector import DataBaseConfig

dbcache: DataBaseConfig | None = None


def getDB() -> DataBaseConfig:
    global dbcache
    if dbcache is None:
        dbcache = DataBaseConfig()
        dbcache.database = "emaildb"
        dbcache.host = "172.18.0.1"
        dbcache.port = 5433
        dbcache.username = "postgres"
        dbcache.password = "Shakalor24"
    return dbcache
