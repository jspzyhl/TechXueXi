import sqlite3
from contextlib import closing


class DB:

    @staticmethod
    def con() -> sqlite3.Connection:
        __con = sqlite3.connect('learn.db')
        __con.row_factory = sqlite3.Row
        return __con


if __name__ == '__main__':
    with DB.con() as con___:
        with closing(con___.cursor()) as cur__:
            cur__.execute(
                'create table if not exists user_info(uid text not null primary key,nickname text,cookies text,article_index integer,video_index integer)')
            cur__.execute(
                'create table if not exists user_cfg(id integer not null primary key autoincrement,last_uid text)')
            cur__.execute('create table if not exists wechat_bind(uid text not null primary key,openid text)')
            cur__.execute('create table if not exists wechat_token(token text,expire_time real)')

        con___.commit()

    # with DB.con() as con___:
    #     with closing(con___.cursor()) as cur_:
    #         d_ = cur_.execute('select cookies from user_info where uid="111"').fetchone()
    #         if d_ and d_['cookies']:
    #             print(d_['cookies'])
