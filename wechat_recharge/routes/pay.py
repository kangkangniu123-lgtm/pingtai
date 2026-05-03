# routes/pay.py
from flask import Blueprint, request, jsonify, session
import datetime
import random
from utils.db import query_one, query_all, execute
from utils.pay_api import unified_order, get_jsapi_params, verify_notify, xml_to_dict
from utils.wechat_api import send_order_paid_notify, get_openid_by_code

pay_bp = Blueprint('pay', __name__)

def make_order_no():
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    rand = str(random.randint(1000, 9999))
    return f"RC{now}{rand}"

@pay_bp.route('/pay/products')
def get_products():
    """获取商品列表（供H5页面调用）"""
    game = request.args.get('game', '')
    if game:
        products = query_all(
            "SELECT id, game_name, name, price, description FROM products WHERE is_active=1 AND game_name=%s ORDER BY sort_order",
            (game,)
        )
    else:
        products = query_all(
            "SELECT id, game_name, name, price, description FROM products WHERE is_active=1 ORDER BY sort_order"
        )
    # 按游戏分组
    games = {}
    for p in products:
        games.setdefault(p['game_name'], []).append({
            'id': p['id'],
            'name': p['name'],
            'price': float(p['price']),
            'description': p['description'],
        })
    return jsonify({'code': 0, 'data': games})

@pay_bp.route('/pay/create', methods=['POST'])
def create_order():
    """创建订单并发起支付"""
    data = request.json
    openid = session.get('openid')
    if not openid:
        return jsonify({'code': -1, 'msg': '请先授权登录'})

    product_id   = data.get('product_id')
    game_account = data.get('game_account', '').strip()
    game_zone    = data.get('game_zone', '').strip()
    game_role    = data.get('game_role', '').strip()
    remark       = data.get('remark', '').strip()

    if not product_id or not game_account:
        return jsonify({'code': -1, 'msg': '请填写完整信息'})

    product = query_one("SELECT * FROM products WHERE id=%s AND is_active=1", (product_id,))
    if not product:
        return jsonify({'code': -1, 'msg': '商品不存在或已下架'})

    order_no = make_order_no()
    amount = product['price']
    amount_fen = int(amount * 100)

    # 写入订单
    execute(
        """INSERT INTO orders
           (order_no, openid, product_id, product_name, game_name, amount,
            game_account, game_zone, game_role, remark)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (order_no, openid, product_id, product['name'], product['game_name'],
         amount, game_account, game_zone, game_role, remark)
    )

    # 调起微信支付
    try:
        ip = request.headers.get('X-Real-IP') or request.remote_addr
        prepay_id = unified_order(openid, order_no, amount_fen, product['name'], ip)
        params = get_jsapi_params(prepay_id)
        return jsonify({'code': 0, 'data': params, 'order_no': order_no})
    except Exception as e:
        return jsonify({'code': -1, 'msg': f'发起支付失败: {str(e)}'})

@pay_bp.route('/pay/notify', methods=['POST'])
def pay_notify():
    """微信支付异步回调"""
    xml_data = request.data
    data = xml_to_dict(xml_data.decode('utf-8'))

    # 验证签名
    if not verify_notify(dict(data)):
        return '<xml><return_code><![CDATA[FAIL]]></return_code></xml>'

    if data.get('result_code') != 'SUCCESS':
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'

    order_no = data.get('out_trade_no')
    transaction_id = data.get('transaction_id')

    order = query_one("SELECT * FROM orders WHERE order_no=%s", (order_no,))
    if order and order['pay_status'] == 0:
        execute(
            "UPDATE orders SET pay_status=1, order_status=1, wx_transaction_id=%s, paid_at=NOW() WHERE order_no=%s",
            (transaction_id, order_no)
        )
        # 通知用户
        try:
            send_order_paid_notify(order['openid'], order)
        except:
            pass

    return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'

@pay_bp.route('/pay/oauth')
def oauth():
    """微信网页授权，获取openid"""
    code = request.args.get('code')
    redirect_url = request.args.get('state', '/')
    if code:
        openid = get_openid_by_code(code)
        if openid:
            session['openid'] = openid
            return f'<script>location.href="{redirect_url}"</script>'
    return '授权失败，请重试', 400

@pay_bp.route('/pay/order/<order_no>')
def order_status(order_no):
    """查询订单状态（前端轮询用）"""
    openid = session.get('openid')
    order = query_one(
        "SELECT order_no, pay_status, order_status, product_name, amount FROM orders WHERE order_no=%s",
        (order_no,)
    )
    if not order:
        return jsonify({'code': -1, 'msg': '订单不存在'})
    return jsonify({'code': 0, 'data': {
        'order_no': order['order_no'],
        'pay_status': order['pay_status'],
        'order_status': order['order_status'],
        'product_name': order['product_name'],
        'amount': float(order['amount']),
    }})
