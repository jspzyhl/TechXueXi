import os
import sqlite3
from contextlib import closing


def __ensure_dir(filepath_: str):
    pass


class DB:
    __db_init = False

    @staticmethod
    def con() -> sqlite3.Connection:
        __con = sqlite3.connect('user/learn.db')
        __con.row_factory = sqlite3.Row
        return __con

    @classmethod
    def init(cls):
        if not cls.__db_init:
            user_dir = os.path.join(os.getcwd(), 'user')
            os.makedirs(user_dir, exist_ok=True)

            with DB.con() as con___:
                with closing(con___.cursor()) as cur__:
                    cur__.execute(
                        'create table if not exists user_info(uid text not null primary key,nickname text,cookies text,article_index integer,video_index integer)')
                    cur__.execute(
                        'create table if not exists user_cfg(id integer not null primary key autoincrement,last_uid text)')
                    cur__.execute('create table if not exists wechat_bind(uid text not null primary key,openid text)')
                    cur__.execute('create table if not exists wechat_token(token text,expire_time real)')

                    cur__.execute('insert or replace into user_info values(0,"default",null,null,null)')
                    cur__.execute('insert or ignore into user_cfg values(1,"0")')
                con___.commit()
            cls.__db_init = True


if __name__ == '__main__':
    # DB.init()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    pass

    # with DB.con() as con___:
    #     with closing(con___.cursor()) as cur_:
    #         d_ = cur_.execute('select cookies from user_info where uid="111"').fetchone()
    #         if d_ and d_['cookies']:
    #             print(d_['cookies'])
