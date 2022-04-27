from pickle import STRING
import requests
import json
from pdlearn.config import cfg_get
from pdlearn import file
import time
from threading import Thread
import os


class WechatHandler:

    def __init__(self):
        if os.getenv('AutoLoginHost') is not None:
            self.auto_login_host = os.getenv('AutoLoginHost')
        else:
            self.auto_login_host = ''

        self.token = []
        self.openid = cfg_get("addition.wechat.openid", "")
        self.appid = cfg_get("addition.wechat.appid", "")
        self.appsecret = cfg_get("addition.wechat.appsecret", "")
        self.token = self.get_access_token()

    def post_token(self):
        if len(self.auto_login_host) > 0:
            url_ = self.auto_login_host + '/wechat/set_token'

            post_dat_ = {'token': self.token[0],
                         'expire_time': self.token[1],
                         'appid': self.appid,
                         }
            requests.post(url=url_, data=json.dumps(post_dat_), timeout=30)
        else:
            print('pdlearn.globalvar.auto_login_host = "" ')

    def get_access_token(self, refresh=False):
        if not refresh:
            # 检查变量
            if self.token and self.token[1] > time.time():
                return self.token
            # 检查文件
            template_json_str = '''[]'''
            token_json_obj = file.get_json_data(
                "user/wechat_token.json", template_json_str)
            if token_json_obj and token_json_obj[1] > time.time():
                self.token = token_json_obj
                return self.token
        # 获取新token
        url_token = 'https://api.weixin.qq.com/cgi-bin/token?'
        res = requests.get(url=url_token, params={
            "grant_type": 'client_credential',
            'appid': self.appid,
            'secret': self.appsecret,
        }).json()
        token = res.get('access_token')
        expires = int(res.get('expires_in')) - 10 + time.time()
        self.token = [token, expires]
        file.save_json_data("user/wechat_token.json", self.token)

        Thread(name='post_token', target=self.post_token).start()

        return self.token

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
        token = self.get_access_token()
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
        token = self.get_access_token()
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
        json_str = '''[]'''
        json_obj = file.get_json_data(
            "user/wechat_bind.json", json_str)
        wx_list = list(
            filter(lambda w: w["accountId"] == uid or w["openId"] == uid, json_obj))
        if wx_list:
            return wx_list[0]["openId"]
        else:
            return self.openid

    def get_uid_by_opendid(self, openid_=None):
        json_str = '''[]'''
        json_obj = file.get_json_data(
            "user/wechat_bind.json", json_str)

        opid = openid_
        if not openid_ or len(openid_) == 0:
            opid = self.openid

        wx_list = list(
            filter(lambda w: w["accountId"] == opid or w["openId"] == opid, json_obj))
        if wx_list:
            return wx_list[0]["accountId"]
        else:
            return ''
