import clickhouse_connect
import os

_client = None

def ch():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(host=os.environ.get("CH_URL","http://clickhouse:8123").split("://")[1].split(":")[0],
                                                port=int(os.environ.get("CH_URL","http://clickhouse:8123").rsplit(':',1)[1]),
                                                database=os.environ.get("CH_DB","default"))
    return _client
