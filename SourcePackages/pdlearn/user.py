from pdlearn import globalvar
import os
import re
import time
import pickle
import base64
import requests
from requests.cookies import RequestsCookieJar
from sys import argv
from pdlearn import score
from pdlearn import file
from pdlearn import color
from pdlearn.mydriver import Mydriver
from pdlearn.exp_catch import exception_catcher
from pdlearn.db_con import *


def get_userId(cookies):
    userId, total, scores, userName = score.get_score(cookies)
    return userId


class UserInfo:
    def __init__(self, uid_: str = '', nickname_: str = '', cookies_: str = ''):
        self.__uid = ''
        self.__nickname = ''
        self.__cookies = ''
        self.uid = uid_
        self.nickname = nickname_
        self.cookies = cookies_

    @property
    def uid(self):
        return self.__uid

    @uid.setter
    def uid(self, u_):
        if u_ is None:
            self.__uid = ''
        else:
            self.__uid = u_

    @property
    def nickname(self):
        return self.__nickname

    @nickname.setter
    def nickname(self, n_):
        if n_ is None:
            self.__nickname = ''
        else:
            self.__nickname = n_

    @property
    def cookies(self):
        return self.__cookies

    @cookies.setter
    def cookies(self, c_):
        if c_ is None:
            self.__cookies = ''
        else:
            self.__cookies = c_

    @property
    def fullname(self) -> str:
        return self.__uid + '_' + self.__nickname


def get_user_info(uid_: str) -> UserInfo:
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('select * from user_info where uid="%s"' % uid_)
            d_ = cur_.fetchone()
            if d_:
                return UserInfo(uid_=d_['uid'], nickname_=d_['nickname'], cookies_=d_['cookies'])
            else:
                return UserInfo()


@exception_catcher(reserve_value="_")
def get_fullname(uid_: str):
    u_inf_ = get_user_info(uid_)
    return u_inf_.fullname


@exception_catcher(reserve_value="")
def get_nickname(uid_: str):
    u_inf_ = get_user_info(uid_)
    return u_inf_.nickname


# def save_fullname(fullname):
#     status = get_user_status()
#     userId = fullname.split('_', 1)[0]
#     nickname = fullname.split('_', 1)[1]
#     status["userId_mapping"][userId] = nickname
#     save_user_status(status)


# def get_user_status():
#     template_json_str = '''{\n    "#-说明1":"此文件是保存用户数据及登陆状态的配置文件",''' + \
#                         '''\n    "#-说明2":"程序会自动读写该文件。",''' + \
#                         '''\n    "#-说明3":"如不熟悉，请勿自行修改内容。错误修改可能导致程序崩溃",''' + \
#                         '''\n    "#____________________________________________________________":"",''' + \
#                         '''\n    "last_userId":0,\n    "userId_mapping":{\n        "0":"default"\n    }\n}'''
#     status = file.get_json_data("user/user_status.json", template_json_str)
#     save_user_status(status)
#     # print(status)
#     return status


def update_last_user(uid_: str):
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('replace into user_cfg values(1,"%s")' % uid_)
        con_.commit()


# def save_user_status(status):
#     file.save_json_data("user/user_status.json", status)


# def get_last_quiz(quiz_type, uid):
#     template_json_str = '''{\n    "#-说明1":"此文件是保存用户最新完成的每周答题和专项答题的配置文件",''' + \
#                         '''\n    "#-说明2":"程序会自动读写该文件。",''' + \
#                         '''\n    "#-说明3":"如不熟悉，请勿自行修改内容。错误修改可能导致程序错误",''' + \
#                         '''\n    "#____________________________________________________________":"",''' + \
#                         '''\n    "weekly":{\n        "0":{"quiz_id":"0","quiz_page":0}\n    },''' + \
#                         '''\n    "zhuanxiang":{\n        "0":"0"\n    }\n}'''
#     status = file.get_json_data("user/last_quiz.json", template_json_str)
#     save_last_quiz(status)
#     # print(status)
#     return None
#
#
# def update_last_quiz(quiz_type, uid, quiz_title_str):
#     pass
#
#
# def save_last_quiz(status):
#     file.save_json_data("user/last_quiz.json", status)

def get_cookie(uid_: str):
    u_inf_ = get_user_info(uid_)
    if len(u_inf_.cookies) > 0:
        cookies_bytes = base64.b64decode(u_inf_.cookies)
        cookie_list = pickle.loads(cookies_bytes)
        for d in cookie_list:  # 检查是否过期
            if 'name' in d and 'value' in d and 'expiry' in d:
                expiry_timestamp = int(d['expiry'])
                if expiry_timestamp > int(time.time()):
                    pass
                else:
                    return []
        return cookie_list
    return []


def save_cookies(cookies):
    uid_ = get_userId(cookies)
    cookies_bytes = pickle.dumps(cookies)
    cookies_b64 = base64.b64encode(cookies_bytes)
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute(
                'update user_info set cookies="%s" where uid="%s"' % (str(cookies_b64, encoding='utf-8'), uid_))
        con_.commit()


def remove_cookie(uid_: str):
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('update user_info set cookies=null where uid="%s"' % uid_)
        con_.commit()


# def get_article_video_json():
#     template_json_str = '''{"#此文件记录用户的视频和文章的浏览进度":"","article_index":{},"video_index":{}}'''
#     article_video_json = file.get_json_data(
#         "user/article_video_index.json", template_json_str)
#     return article_video_json


# def get_index(userId, index_type):
#     article_video_json = get_article_video_json()
#     indexs = article_video_json[index_type]
#     if (str(userId) in indexs.keys()):
#         index = indexs[str(userId)]
#     else:
#         index = 0
#         article_video_json[index_type][str(userId)] = index
#         file.save_json_data(
#             "user/article_video_index.json", article_video_json)
#     return int(index)


# def save_index(userId, index, index_type):
#     article_video_json = get_article_video_json()
#     article_video_json[index_type][str(userId)] = index
#     file.save_json_data("user/article_video_index.json", article_video_json)


def get_article_index(uid_: str) -> int:
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('select article_index from user_info where uid="%s"' % uid_)
            d_ = cur_.fetchone()
            if d_ and d_['article_index']:
                return d_['article_index']
            else:
                return 0


def save_article_index(uid_: str, index_: int):
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('update user_info set article_index=%d where uid="%s"' % (index_, uid_))
        con_.commit()


def get_video_index(uid_: str) -> int:
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('select video_index from user_info where uid="%s"' % uid_)
            d_ = cur_.fetchone()
            if d_ and d_['video_index']:
                return d_['video_index']
            else:
                return 0


def save_video_index(uid_: str, index_: int):
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('update user_info set video_index=%d where uid="%s"' % (index_, uid_))
        con_.commit()


def get_default_userid() -> str:
    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('select * from user_cfg where id=1')
            d_ = cur_.fetchone()
            if d_ and d_['last_uid']:
                return d_['last_uid']
            else:
                return '0'


def get_default_nickname():
    return get_nickname(get_default_userid())


def get_default_fullname():
    return get_fullname(get_default_userid())


def check_default_user_cookie():
    default_userid = get_default_userid()
    default_nickname = get_nickname(default_userid)
    print_list = [color.blue(str(default_userid)),
                  color.blue(default_nickname)]
    print(
        "=" * 60, "\n默认用户ID：{0[0]}，默认用户昵称：{0[1]}".format(print_list), end=" ")
    cookies = get_cookie(default_userid)
    if not cookies:
        print(color.red("【无有效cookie信息，需要登录】"))
        return []
    else:
        print(color.green("（cookie信息有效）"))
        return cookies


# 保活。执行会花费一定时间，全新cookies的有效时间是12h
def refresh_all_cookies(live_time=8.0, display_score=False):  # cookie有效时间保持在live_time以上
    msg_info = {}
    need_check = False
    valid_cookies = []

    with DB.con() as con_:
        with con_.cursor() as cur_:
            cur_.execute('select uid,cookies from user_info')
            l_ = cur_.fetchall()
            for d_ in l_:
                if d_['uid'] and d_['cookies']:
                    uid = d_['uid']
                    cookies_b64 = d_['cookies']
                    cookies_bytes = base64.b64decode(cookies_b64)
                    cookie_list = pickle.loads(cookies_bytes)
                    for d in cookie_list:  # 检查是否过期
                        if 'name' in d and 'value' in d and 'expiry' in d and d["name"] == "token":
                            remain_time = (int(d['expiry']) - int(time.time())) / 3600
                            msg = get_nickname(uid) + " 登录剩余有效时间：" + \
                                  str(int(remain_time * 10) / 10) + " 小时."
                            print(color.green(msg), end="")
                            msg_info[uid] = msg
                            if remain_time < 0:
                                print(color.red(" 已过期 需要重新登陆，将自动移除此cookie."))
                                remove_cookie(uid)
                            else:
                                # print(color.blue(" 有效"), end="")
                                valid_cookies.append(cookie_list)
                                if remain_time <= live_time:  # 全新cookies的有效时间是12h
                                    print(color.red(" 需要刷新"))
                                    need_check = True
                                    # 暂没有证据表明可以用requests来请求，requests请求的响应不带cookies，不确定会不会更新cookies时间
                                    # （但是万一服务端自动更新了cookie，可以试试12h之后再访问呢？则剩余时间直接设为12即可。有空的伙计可以做个实验）
                                    # jar = RequestsCookieJar()
                                    # for cookie in cookie_list:
                                    #     jar.set(cookie['name'], cookie['value'])
                                    # new_cookies = requests.get("https://pc.xuexi.cn/points/my-points.html", cookies=jar,
                                    #                         headers={'Cache-Control': 'no-cache'}).cookies.get_dict()
                                    # 浏览器登陆方式更新cookie，速度较慢但可靠
                                    driver_login = Mydriver(nohead=False)
                                    driver_login.get_url(
                                        "https://www.xuexi.cn/notFound.html")
                                    driver_login.set_cookies(cookie_list)
                                    driver_login.get_url(
                                        'https://pc.xuexi.cn/points/my-points.html')
                                    new_cookies = driver_login.get_cookies()
                                    driver_login.quit()
                                    found_token = False
                                    for j in new_cookies:  # 检查token
                                        if 'name' in j and j["name"] == "token":
                                            found_token = True
                                    if not found_token:
                                        remove_cookie(uid)  # cookie不含token则无效，删除cookie
                                    else:
                                        save_cookies(new_cookies)
                                else:
                                    print(color.green(" 无需刷新"))

    if need_check:  # 再执行一遍来检查有效情况
        print("再次检查cookies有效时间...")
        return refresh_all_cookies(live_time, display_score)
    elif display_score:
        for cookie in valid_cookies:
            user_id = get_userId(cookie)
            print(color.blue(get_fullname(user_id)) + " 的今日得分：")
            total, scores = score.show_score(cookie)
            if str(user_id) in msg_info:
                msg_info[str(user_id)] += " 今日得分：" + str(scores["today"])
    return msg_info


# 如有多用户，打印各个用户信息
def list_user(printing=True):
    with DB.con() as con_:
        with con_.cursor() as cur_:
            map_count = cur_.execute('select * from user_info')
            l_ = cur_.fetchall()
            all_users = []
            for d_ in l_:
                if d_['uid'] == '0':
                    continue
                else:
                    all_users.append([d_['uid'], d_['nickname']])
            if printing:
                if map_count > 2:
                    print("检测到您有多用户：", end="")
                    for d_ in l_:
                        print(color.blue(d_['uid'] + '_' + d_['nickname']), end="; ")
                    print("")
            return all_users


# 多用户中选择一个用户，半成品
def select_user():
    user_list = list_user(printing=False)
    user_count = len(user_list)
    print("=" * 60)
    if user_count > 1:
        print("检测到多用户：")
        for i in range(user_count):
            print(i, " ", user_list[i][0], " ", user_list[i][1])
        num = int(input("请选择用户序号："))
        if num < 0 or num >= user_count:
            print("输入的范围不对。")
            exit()
        else:
            user_id = user_list[num][0]
            print("默认用户已切换为：" + color.blue(get_fullname(user_id)))
            update_last_user(user_id)
    else:
        print("目前你只有一个用户。用户名：", get_default_userid(),
              "，昵称：", get_default_nickname())


# 仅适用于Windows的关机，有待改进
def shutdown(stime):
    if stime:
        stime = int(stime)
        os.system('shutdown -s -t {}'.format(stime))
        for i in range(stime):
            print("\r{}秒后关机".format(stime - i), end="")
            time.sleep(1)
    else:
        print("无自动关机任务，已释放程序内存，窗口将自动关闭")
        # time.sleep(600)
        # os.system("timeout 60")
