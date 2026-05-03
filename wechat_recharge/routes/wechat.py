# routes/wechat.py
from flask import Blueprint, request, make_response
from utils.wechat_api import verify_signature, parse_xml_message, build_text_reply
from utils.db import query_one, execute
import datetime

wechat_bp = Blueprint('wechat', __name__)

HELP_TEXT = """欢迎使用游戏代充服务！🎮

回复以下关键词操作：
【商品列表】查看所有游戏充值商品
【我的订单】查看最近订单
【帮助】显示此菜单

客服时间：9:00-22:00
如有问题请直接留言"""

@wechat_bp.route('/wechat', methods=['GET', 'POST'])
def wechat():
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echostr = request.args.get('echostr', '')

    # 微信服务器验证
    if request.method == 'GET':
        if verify_signature(signature, timestamp, nonce):
            return echostr
        return 'error', 403

    # 处理消息
    if not verify_signature(signature, timestamp, nonce):
        return 'error', 403

    msg = parse_xml_message(request.data)
    openid = msg.get('FromUserName')
    to_user = msg.get('ToUserName')
    msg_type = msg.get('MsgType')

    # 保存/更新用户
    _save_user(openid)

    reply_content = None

    if msg_type == 'event':
        event = msg.get('Event', '').lower()
        if event == 'subscribe':
            reply_content = f"感谢关注！👋\n\n{HELP_TEXT}"
        elif event == 'click':
            key = msg.get('EventKey', '')
            reply_content = _handle_menu_click(key, openid)

    elif msg_type == 'text':
        content = msg.get('Content', '').strip()
        reply_content = _handle_text(content, openid)

    if reply_content:
        xml = build_text_reply(openid, to_user, reply_content)
        resp = make_response(xml)
        resp.content_type = 'application/xml'
        return resp

    return 'success'


def _save_user(openid):
    existing = query_one("SELECT id FROM users WHERE openid=%s", (openid,))
    if not existing:
        execute("INSERT INTO users (openid) VALUES (%s)", (openid,))


def _handle_text(content, openid):
    if content in ['帮助', 'help', '菜单']:
        return HELP_TEXT

    if content == '商品列表':
        return _get_product_list()

    if content in ['我的订单', '订单查询']:
        return _get_my_orders(openid)

    # 查询指定订单 格式: #订单ORDER_NO
    if content.startswith('#订单'):
        order_no = content.replace('#订单', '').strip()
        return _query_order_detail(order_no, openid)

    return f"收到您的消息：{content}\n\n{HELP_TEXT}"


def _handle_menu_click(key, openid):
    if key == 'PRODUCTS':
        return _get_product_list()
    if key == 'MY_ORDERS':
        return _get_my_orders(openid)
    if key == 'HELP':
        return HELP_TEXT
    return HELP_TEXT


def _get_product_list():
    from utils.db import query_all
    products = query_all(
        "SELECT game_name, name, price, description FROM products WHERE is_active=1 ORDER BY sort_order, id"
    )
    if not products:
        return "暂无商品，请稍后再试"

    # 按游戏分组
    games = {}
    for p in products:
        games.setdefault(p['game_name'], []).append(p)

    lines = ["🎮 游戏充值商品列表\n"]
    for game, items in games.items():
        lines.append(f"━━ {game} ━━")
        for item in items:
            lines.append(f"• {item['name']}  ¥{item['price']}")
    lines.append("\n点击下方菜单「立即充值」下单")
    return '\n'.join(lines)


def _get_my_orders(openid):
    from utils.db import query_all
    orders = query_all(
        """SELECT order_no, product_name, amount, order_status, created_at
           FROM orders WHERE openid=%s ORDER BY created_at DESC LIMIT 5""",
        (openid,)
    )
    if not orders:
        return "您还没有订单记录"

    status_map = {0: '待支付', 1: '处理中', 2: '已完成', 3: '已退款'}
    lines = ["📋 最近5条订单\n"]
    for o in orders:
        status = status_map.get(o['order_status'], '未知')
        dt = o['created_at'].strftime('%m-%d %H:%M') if o['created_at'] else ''
        lines.append(f"[{dt}] {o['product_name']}")
        lines.append(f"¥{o['amount']} | {status} | {o['order_no']}\n")
    return '\n'.join(lines)


def _query_order_detail(order_no, openid):
    order = query_one(
        "SELECT * FROM orders WHERE order_no=%s AND openid=%s", (order_no, openid)
    )
    if not order:
        return f"未找到订单：{order_no}"

    status_map = {0: '⏳待处理', 1: '🔄处理中', 2: '✅已完成', 3: '↩已退款'}
    pay_map = {0: '未支付', 1: '已支付'}
    return (
        f"订单详情\n"
        f"━━━━━━━━\n"
        f"订单号：{order['order_no']}\n"
        f"商品：{order['product_name']}\n"
        f"游戏：{order['game_name']}\n"
        f"账号：{order['game_account']}\n"
        f"金额：¥{order['amount']}\n"
        f"支付：{pay_map.get(order['pay_status'])}\n"
        f"状态：{status_map.get(order['order_status'])}\n"
        f"时间：{order['created_at'].strftime('%Y-%m-%d %H:%M')}"
    )
