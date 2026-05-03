# utils/wechat_api.py
import requests
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from config import Config
from utils.db import query_one, execute

def get_access_token():
    """获取access_token，带缓存"""
    row = query_one("SELECT token, expires_at FROM wx_token_cache ORDER BY id DESC LIMIT 1")
    if row and row['expires_at'] > datetime.now():
        return row['token']

    # 重新获取
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={Config.WECHAT_APPID}&secret={Config.WECHAT_APPSECRET}"
    resp = requests.get(url).json()
    token = resp.get('access_token')
    if not token:
        raise Exception(f"获取access_token失败: {resp}")

    expires_at = datetime.now() + timedelta(seconds=7000)
    execute("DELETE FROM wx_token_cache")
    execute("INSERT INTO wx_token_cache (token, expires_at) VALUES (%s, %s)", (token, expires_at))
    return token

def get_openid_by_code(code):
    """通过code换取openid"""
    url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={Config.WECHAT_APPID}&secret={Config.WECHAT_APPSECRET}&code={code}&grant_type=authorization_code"
    resp = requests.get(url).json()
    return resp.get('openid')

def send_text_message(openid, content):
    """发送文本客服消息"""
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={token}"
    data = {
        "touser": openid,
        "msgtype": "text",
        "text": {"content": content}
    }
    requests.post(url, json=data)

def send_order_paid_notify(openid, order):
    """支付成功后通知用户"""
    msg = (
        f"✅ 支付成功！\n\n"
        f"订单号：{order['order_no']}\n"
        f"商品：{order['product_name']}\n"
        f"游戏账号：{order['game_account']}\n"
        f"金额：¥{order['amount']}\n\n"
        f"我们将尽快为您充值，请耐心等待～\n"
        f"查询订单回复：#订单{order['order_no']}"
    )
    send_text_message(openid, msg)

def send_order_complete_notify(openid, order):
    """充值完成后通知用户"""
    msg = (
        f"🎉 充值已完成！\n\n"
        f"订单号：{order['order_no']}\n"
        f"商品：{order['product_name']}\n"
        f"游戏账号：{order['game_account']}\n\n"
        f"感谢您的惠顾，欢迎下次光临！"
    )
    send_text_message(openid, msg)

def verify_signature(signature, timestamp, nonce):
    """验证微信消息签名"""
    items = sorted([Config.WECHAT_TOKEN, timestamp, nonce])
    sha1 = hashlib.sha1(''.join(items).encode()).hexdigest()
    return sha1 == signature

def parse_xml_message(xml_data):
    """解析微信推送的XML消息"""
    root = ET.fromstring(xml_data)
    return {child.tag: child.text for child in root}

def build_text_reply(to_user, from_user, content):
    """构建文本回复XML"""
    import time
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""

def get_jsapi_ticket():
    """获取jsapi_ticket用于网页授权"""
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={token}&type=jsapi"
    resp = requests.get(url).json()
    return resp.get('ticket')
