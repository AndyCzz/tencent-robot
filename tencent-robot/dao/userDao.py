import sys

from sqlalchemy import BIGINT
sys.path.append('/Users/andy/Desktop/tencent-robot/tencent-robot')
from utils.dbUtil import getDB, closeDB
from pojo.User import User
import datetime


def insertUser(user):
    conn = getDB()
    cursor = conn.cursor()
    sql = "insert into robot_user(id, poetry_score, num_score, visit_time) values(%s, %d, %d, '%s')"
    
    cursor.execute(sql%(str(user.id), user.poetry_score, user.num_score, user.visit_time))
    conn.commit()
    closeDB(cursor, conn)

def updateUser(user):
    conn = getDB()
    cursor = conn.cursor()
    sql = "update robot_user set poetry_score=%d, num_score=%d where id=%s"
    
    cursor.execute(sql%(user.poetry_score, user.num_score, str(user.id)))
    conn.commit()
    closeDB(cursor, conn)
    
def selectById(id):
    conn = getDB()
    cursor = conn.cursor()
    sql = "select * from robot_user where id=%s"
    count = cursor.execute(sql%(str(id)))
    res = cursor.fetchone()
    conn.commit()
    closeDB(cursor, conn)
    return res
    
if __name__ == '__main__':
    user = User(15570215553774643260, 1, 1, datetime.datetime.now().strftime("%Y-%m-%d"))
    # insertUser(user)
    # selectById(0)
    user.poetry_score = 2
    user.num_score = 2
    print(not 0)
    # updateUser(user)
    
