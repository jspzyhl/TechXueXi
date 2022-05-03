import os
import pymysql
from pymysql.cursors import *
from dbutils.pooled_db import PooledDB


class DB:
    __con_pool: PooledDB = None

    @classmethod
    def con(cls) -> pymysql.connections.Connection:
        return cls.__con_pool.connection()

    @classmethod
    def init(cls, mincached_: int = 2):
        if not cls.__con_pool:
            cls.__con_pool = PooledDB(creator=pymysql,
                                      mincached=mincached_,
                                      ping=0,
                                      host='localhost',
                                      port=3306,
                                      user='root',
                                      password='1234',
                                      database='learn',
                                      charset='utf8mb4',
                                      cursorclass=DictCursor
                                      )
            with DB.con() as con_:
                with con_.cursor() as cur_:
                    cur_.execute('select * from user_info where uid=0')
                    d_ = cur_.fetchone()
                    if d_:
                        print(d_['nickname'])


if __name__ == '__main__':
    DB.init()
