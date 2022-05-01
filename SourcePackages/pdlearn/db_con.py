import os
import sqlite3
from contextlib import closing


class DB:
    __db_init = False
    __db_path = ''

    @staticmethod
    def __ensure_dir(filepath_: str):
        dir_ = os.path.dirname(filepath_)
        os.makedirs(dir_, exist_ok=True)

    @classmethod
    def con(cls) -> sqlite3.Connection:
        __con = sqlite3.connect(cls.__db_path, timeout=30)
        __con.row_factory = sqlite3.Row
        return __con

    @classmethod
    def init(cls):
        if not cls.__db_init:
            cls.__db_path = os.path.join(os.getcwd(), 'user')
            cls.__db_path = os.path.join(cls.__db_path, 'learn.db')
            DB.__ensure_dir(cls.__db_path)

            with DB.con() as con___:
                with closing(con___.cursor()) as cur__:
                    cur__.execute(
                        'create table if not exists user_info(uid text not null primary key,nickname text,cookies text,article_index integer,video_index integer)')
                    cur__.execute(
                        'create table if not exists user_cfg(id integer not null primary key autoincrement,last_uid text)')
                    cur__.execute('create table if not exists wechat_bind(uid text not null primary key,openid text)')
                    cur__.execute('create table if not exists wechat_token(token text,expire_time real)')
                    cur__.execute(
                        'create table if not exists wechat_privilege(openid text not null primary key,admin int)')

                    cur__.execute('insert or replace into user_info values(0,"default",null,null,null)')
                    cur__.execute('insert or ignore into user_cfg values(1,"0")')
                con___.commit()
            cls.__db_init = True


if __name__ == '__main__':
    DB.init()

    # with DB.con() as con___:
    #     with closing(con___.cursor()) as cur_:
    #         d_ = cur_.execute('delete from wechat_bind where openid="aaa"').fetchone()
    #         if d_:
    #             print(dict(d_))
    #     con___.commit()
    #     print(con___.total_changes)
