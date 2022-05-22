import yaml
import pymysql
from dbutils.pooled_db import PooledDB
import redis

with open("./config/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)

# mysql的配置
db_host = config["database"]["mysql"]["url"]
db_port = config["database"]["mysql"]["port"]
db_user = config["database"]["mysql"]["user"]
db_passwd = config["database"]["mysql"]["password"]

# redis的配置
redis_host = config["database"]["redis"]["url"]
redis_port = config["database"]["redis"]["port"]

def getDB():
    # conn = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd, db='practice', port=db_port, charset='utf8mb4')
    pool = PooledDB(pymysql, 5, host=db_host, user=db_user, passwd=str(db_passwd), db='practice', port=int(db_port), charset='utf8mb4')
    conn = pool.connection()
    return conn

def closeDB(cursor, conn):
    cursor.close()
    conn.close()

def getRedisInstance():
    pool = redis.ConnectionPool(host=redis_host, port=int(redis_port), decode_responses=True)
    return redis.Redis(connection_pool=pool)
  
