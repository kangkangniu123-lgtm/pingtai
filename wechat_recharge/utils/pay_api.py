# utils/pay_api.py
import hashlib
import random
import string
import time
import requests
import xml.etree.ElementTree as ET
from config import Config

def random_str(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def dict_to_xml(data):
    xml = ['<xml>']
    for k, v in data.items():
        xml.append(f'<{k}><![CDATA[{v}]]></{k}>')
    xml.append('</xml>')
    return ''.join(xml)

def xml_to_dict(xml_str):
    root = ET.fromstring(xml_str)
    return {child.tag: child.text for child in root}

def sign(data):
    """微信支付签名"""
    # 按key排序拼接
    items = sorted(data.items())
    query = '&'.join(f'{k}={v}' for k, v in items if v)
    query += f'&key={Config.MCH_KEY}'
    return hashlib.md5(query.encode('utf-8')).hexdigest().upper()

def unified_order(openid, order_no, amount_fen, body, ip):
    """统一下单（JSAPI支付）
    amount_fen: 金额，单位分
    """
    nonce = random_str()
    data = {
        'appid': Config.WECHAT_APPID,
        'mch_id': Config.MCH_ID,
        'nonce_str': nonce,
        'body': body,
        'out_trade_no': order_no,
        'total_fee': str(amount_fen),
        'spbill_create_ip': ip,
        'notify_url': Config.NOTIFY_URL,
        'trade_type': 'JSAPI',
        'openid': openid,
    }
    data['sign'] = sign(data)
    xml_data = dict_to_xml(data)

    resp = requests.post(
        'https://api.mch.weixin.qq.com/pay/unifiedorder',
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'application/xml'},
        timeout=10
    )
    result = xml_to_dict(resp.text)
    if result.get('return_code') != 'SUCCESS' or result.get('result_code') != 'SUCCESS':
        raise Exception(f"统一下单失败: {result}")
    return result['prepay_id']

def get_jsapi_params(prepay_id):
    """获取前端调起支付需要的参数"""
    nonce = random_str()
    ts = str(int(time.time()))
    pkg = f'prepay_id={prepay_id}'
    data = {
        'appId': Config.WECHAT_APPID,
        'timeStamp': ts,
        'nonceStr': nonce,
        'package': pkg,
        'signType': 'MD5',
    }
    data['paySign'] = sign(data)
    return data

def verify_notify(data):
    """验证支付回调签名"""
    sign_received = data.pop('sign', None)
    expected = sign(data)
    return expected == sign_received

def query_order(order_no):
    """查询订单支付状态"""
    nonce = random_str()
    data = {
        'appid': Config.WECHAT_APPID,
        'mch_id': Config.MCH_ID,
        'out_trade_no': order_no,
        'nonce_str': nonce,
    }
    data['sign'] = sign(data)
    xml_data = dict_to_xml(data)
    resp = requests.post(
        'https://api.mch.weixin.qq.com/pay/orderquery',
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'application/xml'},
        timeout=10
    )
    return xml_to_dict(resp.text)
