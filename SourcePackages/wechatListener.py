from hashlib import sha1
import os
import time
from flask import Flask, request
import requests
import json
from typing import *
from threading import Thread
from threading import Lock

from selenium.webdriver.support import ui
from pdlearn.config import cfg_get
from pdlearn.wechat import WechatHandler
from pdlearn.threads import MyThread
from pdlearn import file
import pandalearning as pdl
from pdlearn import globalvar as gl


class ThreadList:
    def __init__(self):
        self.threads: List[Thread] = []

    def add(self, name_, func_, *args_):
        self.threads.append(Thread(target=func_, name=name_, args=args_))

    def run(self):
        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()


app = Flask(__name__)
appid = cfg_get("addition.wechat.appid", "")
appsecret = cfg_get("addition.wechat.appsecret", "")
token = cfg_get("addition.wechat.token", "")
openid = cfg_get("addition.wechat.openid", "")
wechat = WechatHandler()


class MessageInfo:
    to_user_name = ""
    from_user_name = ""
    create_time = ""
    msg_type = ""
    content = ""
    msg_id = ""
    event = ""
    event_key = ""

    def __init__(self, root):
        for child in root:
            if child.tag == 'ToUserName':
                self.to_user_name = child.text
            elif child.tag == 'FromUserName':
                self.from_user_name = child.text
            elif child.tag == 'CreateTime':
                self.create_time = child.text
            elif child.tag == 'MsgType':
                self.msg_type = child.text
            elif child.tag == 'Content':
                self.content = child.text
            elif child.tag == 'MsgId':
                self.msg_id = child.text
            elif child.tag == 'Event':
                self.event = child.text
            elif child.tag == 'EventKey':
                self.event_key = child.text

    def returnXml(self, msg, msg_type="text"):
        return f"<xml><ToUserName><![CDATA[{self.from_user_name}]]></ToUserName><FromUserName><![CDATA[{self.to_user_name}]]></FromUserName><CreateTime>{time.time()}</CreateTime><MsgType><![CDATA[{msg_type}]]></MsgType><Content><![CDATA[{msg}]]></Content></xml>"


def get_update(timestamp, nonce):
    arguments = ''
    for k in sorted([token, timestamp, nonce]):
        arguments = arguments + str(k)
    m = sha1()
    m.update(arguments.encode('utf8'))
    return m.hexdigest()


def check_signature():
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    check = get_update(timestamp, nonce)
    return True if check == signature else False


def parse_xml(data):
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET
    root = ET.fromstring(data)
    return MessageInfo(root)


def wechat_init(msg: MessageInfo):
    """
    初始化订阅号菜单
    """
    url = "https://api.weixin.qq.com/cgi-bin/menu/create?"
    body = {
        "button": [
            {
                "type": "click",
                "name": "开始学xi",
                "key": "MENU_LEARN"
            },
            {
                "name": "我的",
                "sub_button": [
                    {
                        "type": "click",
                        "name": "今日积分",
                        "key": "MENU_SCORE"
                    },
                    {
                        "type": "click",
                        "name": "账号编码",
                        "key": "MENU_OPENID"
                    },
                ]
            }
        ]
    }

    res = requests.post(url=url, params={
        'access_token': wechat.get_access_token()
    }, data=json.dumps(body, ensure_ascii=False).encode('utf-8')).json()
    if res.get("errcode") == 0:
        return msg.returnXml("菜单初始化成功，请重新关注订阅号")
    else:
        return msg.returnXml(res.get("errmsg"))


def get_uid(oid):
    json_str = '''[]'''
    json_obj = file.get_json_data(
        "user/wechat_bind.json", json_str)
    wx_list = list(filter(lambda w: w["openId"] == oid, json_obj))
    if wx_list:
        return wx_list[0]["accountId"]
    else:
        return ""


def wechat_get_openid(msg: MessageInfo):
    """
    获取用户的openId
    """
    return msg.returnXml(msg.from_user_name)


def wechat_get_score(msg: MessageInfo):
    """
    获取今日分数
    """
    uid = get_uid(msg.from_user_name)
    if not uid:
        wechat.send_text("您未绑定账号，请联系管理员绑定", uid=msg.from_user_name)
    else:
        score = pdl.get_my_score(uid)
        if not score:
            wechat.send_text("登录过期，请重新登录后再试", msg.from_user_name)
            pdl.add_user(msg.from_user_name)


def wechat_help(msg: MessageInfo):
    """
    获取帮助菜单
    """
    return msg.returnXml(
        "/help 显示帮助消息\n/init 初始化订阅号菜单，仅需要执行一次\n/add 添加新账号\n/bind 绑定账号，如：/bind 账号编码 学xi编号\n/unbind 解除绑定 如：/unbind 账号编码\n/list 获取全部账号信息\n/update 更新程序\n/login 添加自动扫码账号\n/authcode 提交短信验证码\n/grant 授权微信账号\n/revoke 撤销微信账号")


def wechat_add():
    """
    添加新账号
    """
    pdl.add_user()


def wechat_bind(msg: MessageInfo):
    """
    绑定微信号
    """
    args = msg.content.split(" ")
    if len(args) == 3:
        json_str = '''[]'''
        json_obj = file.get_json_data(
            "user/wechat_bind.json", json_str)
        wx_list = list(filter(lambda w: w["openId"] == args[1], json_obj))
        if wx_list:
            index = json_obj.index(wx_list[0])
            json_obj[index]["accountId"] = args[2]
        else:
            json_obj.append({"openId": args[1], "accountId": args[2]})
        file.save_json_data("user/wechat_bind.json", json_obj)
        return msg.returnXml("绑定成功")
    else:
        return msg.returnXml("参数格式错误")


def wechat_unbind(msg: MessageInfo):
    """
    解绑微信号
    """
    args = msg.content.split(" ")
    if len(args) == 2:
        json_str = '''[]'''
        json_obj = file.get_json_data(
            "user/wechat_bind.json", json_str)
        wx_list = list(filter(lambda w: w["openId"] == args[1], json_obj))
        if wx_list:
            index = json_obj.index(wx_list[0])
            json_obj.pop(index)
            file.save_json_data("user/wechat_bind.json", json_obj)
            return msg.returnXml("解绑成功")
        else:
            return msg.returnXml("账号编码错误或该编码未绑定账号")
    else:
        return msg.returnXml("参数格式错误")


def wechat_list(msg: MessageInfo):
    """
    获取全部成员
    """
    msg = pdl.get_user_list()
    wechat.send_text(msg)


def wechat_admin_learn(msg: MessageInfo):
    """
    学习
    """


def wechat_update(msg: MessageInfo):
    res = ""
    try:
        shell = "git -C /xuexi/code/TechXueXi pull $Sourcepath $pullbranche "
        params = msg.content.split(" ")
        if len(params) > 1:
            shell += params[1]
        msg = os.popen(shell).readlines()[-1]
        if "up to date" in msg:
            res = "当前代码已经是最新的了"
        else:
            os.popen("cp -r /xuexi/code/TechXueXi/SourcePackages/* /xuexi")
            res = "代码更新完成" + msg
    except Exception as e:
        res = "更新失败：" + str(e)
    wechat.send_text(res)


def is_valid_user(openid_: str) -> bool:
    if openid_ == openid:
        return True
    json_str = '''[]'''
    json_obj = file.get_json_data(
        "user/wechat_grant.json", json_str)
    wx_list = list(filter(lambda w: w == openid_, json_obj))
    if wx_list:
        return True
    else:
        return False


def wechat_login(msg: MessageInfo):
    """
    登录xx账号
    """
    if is_valid_user(msg.from_user_name):
        args = msg.content.split(" ")
        if len(args) == 3:
            phonenum_ = args[1]
            password_ = args[2]
            if len(gl.auto_login_host) > 0:
                url_ = gl.auto_login_host + '/xx/add_account'

                post_dat_ = {'phonenum': phonenum_,
                             'password': password_,
                             'openid': msg.from_user_name,
                             }
                try:
                    respon_ = requests.post(url=url_, data=json.dumps(post_dat_), timeout=270).json()
                    print(respon_)
                    login_result_ = respon_['login_result']
                    if login_result_ == 'success':
                        return msg.returnXml("登录成功")
                    elif login_result_ == 'auth_code':
                        return msg.returnXml('需要验证，请发送“/authcode 验证码” 提交短信验证码')
                except Exception as e:
                    return msg.returnXml('登录失败，出现错误。')
            else:
                return msg.returnXml('登录失败，未设置自动登录服务')
        else:
            return msg.returnXml("参数格式错误，正确格式：/login 手机号码 密码")
    else:
        return msg.returnXml("当前微信号没有执行此命令的权限，请联系管理员授权")


def wechat_authcode(msg: MessageInfo):
    """
    提交验证码
    """
    args = msg.content.split(" ")
    if len(args) == 2:
        authcode_ = args[1]
        if len(gl.auto_login_host) > 0:
            url_ = gl.auto_login_host + '/xx/set_auth_code'

            post_dat_ = {'auth_code': authcode_,
                         'openid': msg.from_user_name,
                         }
            try:
                requests.post(url=url_, data=json.dumps(post_dat_), timeout=60).json()
            except Exception as e:
                return msg.returnXml('出现错误，提交失败。')
    else:
        return msg.returnXml("参数格式错误，正确格式：“/authcode 验证码”")


def wechat_grant(msg: MessageInfo):
    """
    授权微信号
    """
    if msg.from_user_name == openid:
        args = msg.content.split(" ")
        if len(args) == 2:
            json_str = '''[]'''
            json_obj = file.get_json_data(
                "user/wechat_grant.json", json_str)
            wx_list = list(filter(lambda w: w == args[1], json_obj))
            if not wx_list:
                json_obj.append(args[1])

            file.save_json_data("user/wechat_grant.json", json_obj)
            return msg.returnXml("授权成功")
        else:
            return msg.returnXml("参数格式错误")


def wechat_revoke(msg: MessageInfo):
    """
    撤销微信号
    """
    if msg.from_user_name == openid:
        args = msg.content.split(" ")
        if len(args) == 2:
            json_str = '''[]'''
            json_obj = file.get_json_data(
                "user/wechat_grant.json", json_str)
            wx_list = list(filter(lambda w: w == args[1], json_obj))
            if wx_list:
                index = json_obj.index(wx_list[0])
                json_obj.pop(index)
                file.save_json_data("user/wechat_grant.json", json_obj)
                return msg.returnXml("撤销成功")
            else:
                return msg.returnXml("账号编码错误或该编码未被授权")
        else:
            return msg.returnXml("参数格式错误")


@app.route('/wechat', methods=['GET', 'POST'])
def weixinInterface():
    if check_signature:
        if request.method == 'GET':
            echostr = request.args.get('echostr', '')
            return echostr
        elif request.method == 'POST':
            data = request.data
            msg = parse_xml(data)
            if msg.msg_type == "event" and msg.event == "CLICK":
                if msg.event_key == "MENU_OPENID":
                    return wechat_get_openid(msg)
                if msg.event_key == "MENU_LEARN":
                    uid_ = get_uid(msg.from_user_name)
                    if not uid_:
                        return msg.returnXml("初次使用，请发送 “/login 手机号码 密码” 进行账号登录")
                    else:
                        MyThread("wechat_learn", pdl.start, uid_).start()
                if msg.event_key == "MENU_SCORE":
                    MyThread("wechat_get_score", wechat_get_score, msg).start()
            if msg.from_user_name == openid:
                if msg.content.startswith("/init"):
                    return wechat_init(msg)
                if msg.content.startswith("/help"):
                    return wechat_help(msg)
                if msg.content.startswith("/bind"):
                    return wechat_bind(msg)
                if msg.content.startswith("/unbind"):
                    return wechat_unbind(msg)
                if msg.content.startswith("/add"):
                    MyThread("wechat_add", wechat_add).start()
                if msg.content.startswith("/list"):
                    MyThread("wechat_list", wechat_list, msg).start()
                if msg.content.startswith("/learn"):
                    MyThread("wechat_admin_learn", wechat_admin_learn, msg).start()
                # if msg.content.startswith("/update"):
                #     MyThread("wechat_update", wechat_update, msg).start()
                if msg.content.startswith("/login"):
                    MyThread("login", wechat_login, msg).start()
                if msg.content.startswith("/authcode"):
                    MyThread("authcode", wechat_authcode, msg).start()
                if msg.content.startswith("/grant"):
                    return wechat_grant(msg)
                if msg.content.startswith("/revoke"):
                    return wechat_revoke(msg)

            return "success"
    else:
        return 'signature error'


app2 = Flask(__name__)


@app2.route("/token_request", methods=['POST'])
def token_request():
    req_dat_ = json.loads(request.data)
    token_ = ''
    expire_ = 0
    if req_dat_['refresh']:
        token_, expire_ = wechat.get_access_token(True)
    else:
        token_, expire_ = wechat.get_access_token(False)
        Thread(name='post_token_app2', target=wechat.post_token).start()

    resp_dat_ = {'state': 'ok',
                 'token': token_,
                 'expire': expire_
                 }
    return json.dumps(resp_dat_)


def run_app1():
    app.run('0.0.0.0', 8088)


def run_app2():
    app2.run('0.0.0.0', 8089)


if __name__ == '__main__':
    th_list = ThreadList()
    th_list.add('app1', run_app1)
    th_list.add('app2', run_app2)
    th_list.run()
