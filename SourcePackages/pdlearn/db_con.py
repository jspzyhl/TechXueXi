import os
import pymysql
from pymysql.cursors import *
from dbutils.pooled_db import PooledDB
import socket
import time


def wait_for_port(port, host='localhost', timeout=5.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError('Waited too long for the port {} on host {} to start accepting '
                                   'connections.'.format(port, host)) from ex


class DB:
    __con_pool: PooledDB = None

    @classmethod
    def con(cls) -> pymysql.connections.Connection:
        return cls.__con_pool.connection()

    @classmethod
    def init(cls, mincached_: int = 2):
        if not cls.__con_pool:
            wait_for_port(3306, 'localhost', 60)
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
            # with DB.con() as con_:
            #     with con_.cursor() as cur_:
            #         cur_.execute('select * from user_info where uid=0')
            #         d_ = cur_.fetchone()
            #         if d_:
            #             print(d_['nickname'])
            #         cur_.execute('update user_info set article_index=0 where uid=0')
            #     con_.commit()


if __name__ == '__main__':
    DB.init()
