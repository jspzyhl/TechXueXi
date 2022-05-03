from pickle import STRING
import requests
import json
from pdlearn.config import *
from pdlearn import file
import time
from threading import Thread
import os
from pdlearn.db_con import *


class TokenCache:
    def __init__(self, token_: str = '', expire_: float = 0):
        self.token: str = token_
        self.expire_time: float = expire_


class WechatHandler:

    def __init__(self):

        self.auto_login_host = get_env_or_cfg('.', 'auto_login_host', '')
        self.openid = get_env_or_cfg('.', 'wechat_openid', '')
        self.appid = get_env_or_cfg('.', 'wechat_appid', '')
        self.appsecret = get_env_or_cfg('.', 'wechat_appsecret', '')
        self.token_cache = TokenCache()

    def post_token(self):
        if len(self.auto_login_host) > 0:
            url_ = self.auto_login_host + '/wechat/set_token'

            post_dat_ = {'token': self.token_cache.token,
                         'expire_time': self.token_cache.expire_time,
                         'appid': self.appid,
                         }
            requests.post(url=url_, data=json.dumps(post_dat_), timeout=30)
        # else:
        #     print('pdlearn.globalvar.auto_login_host = "" ')

    def get_access_token(self, refresh=False):
        if not refresh:
            # 检查变量
            if self.token_cache.token and self.token_cache.expire_time > time.time():
                return self.token_cache
            # 检查文件
            with DB.con() as con_:
                with con_.cursor() as cur_:
                    cur_.execute('select * from wechat_token where id=1')
                    d_ = cur_.fetchone()
                    if d_:
                        token_ = d_['token']
                        exp_ = d_['expire_time']
                        if token_ and exp_ > time.time():
                            self.token_cache = TokenCache(token_, exp_)
                            return self.token_cache

        # 获取新token
        assert self.appid and self.appsecret, '环境变量：wechat_appid 或 wechat_appsecret 未设置'

        url_token = 'https://api.weixin.qq.com/cgi-bin/token?'
        res = requests.get(url=url_token, params={
            "grant_type": 'client_credential',
            'appid': self.appid,
            'secret': self.appsecret,
        }).json()
        token = res.get('access_token')
        expires = int(res.get('expires_in')) - 10 + time.time()
        self.token_cache = TokenCache(token, expires)
        with DB.con() as con_:
            with con_.cursor() as cur_:
                cur_.execute('replace into wechat_token values(1,"%s",%f)' % (token, expires))
                print(token, expires)
            con_.commit()

        Thread(name='post_token', target=self.post_token).start()
        return self.token_cache

    def send_text(self, text: STRING, uid=""):
        if not uid:
            uid = self.openid
        if text.startswith("http") or text.startswith("dtxuexi"):
            login_tempid = cfg_get("addition.wechat.login_tempid", "")
            if login_tempid:
                return self.send_template(login_tempid, {"name": {"value": "用户"}}, uid, text)
        if "当前学 xi 总积分" in text:
            login_tempid = cfg_get("addition.wechat.score_tempid", "")
            if login_tempid:
                return self.send_template(login_tempid, {"score": {"value": text}}, uid, "")
        token = self.get_access_token().token
        url_msg = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?'
        body = {
            "touser": uid,
            "msgtype": "text",
            "text": {
                "content": text
            }
        }
        res = requests.post(url=url_msg, params={
            'access_token': token
        }, data=json.dumps(body, ensure_ascii=False).encode('utf-8')).json()
        print(res)
        if res["errcode"] == 40001:
            self.get_access_token(True)
            self.send_text(text, uid)

    def send_template(self, id, temp_data, uid, url):
        post_url = "https://api.weixin.qq.com/cgi-bin/message/template/send?"
        token = self.get_access_token().token
        body = {
            "touser": uid,
            "url": url,
            "template_id": id,
            "data": temp_data
        }
        res = requests.post(url=post_url, params={
            'access_token': token
        }, data=json.dumps(body, ensure_ascii=False).encode('utf-8')).json()
        print(res)
        if res["errcode"] == 40001:
            self.get_access_token(True)
            self.send_template(id, temp_data, uid, url)

    def get_opendid_by_uid(self, uid):
        """
        账号换绑定的openid，没有则返回主账号
        """
        with DB.con() as con_:
            with con_.cursor() as cur_:
                cur_.execute('select * from wechat_bind where uid="%s"' % uid)
                d_ = cur_.fetchone()
                if d_ and d_['openid']:
                    return d_['openid']
                else:
                    return self.openid
