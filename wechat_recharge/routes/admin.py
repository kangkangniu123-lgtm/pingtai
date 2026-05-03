from flask import Blueprint, request, jsonify, session, render_template
from functools import wraps
from config import Config
from utils.db import query_one, query_all, execute
from utils.wechat_api import send_order_complete_notify
import os, uuid

admin_bp = Blueprint('admin', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/admin')
def admin_index():
    return render_template('admin/index.html')

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('username') == Config.ADMIN_USERNAME and data.get('password') == Config.ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({'code': 0, 'msg': '登录成功'})
    return jsonify({'code': -1, 'msg': '用户名或密码错误'})

@admin_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'code': 0})

@admin_bp.route('/admin/stats')
@login_required
def stats():
    today = query_one("SELECT COUNT(*) as cnt, IFNULL(SUM(amount),0) as total FROM orders WHERE DATE(created_at)=CURDATE() AND pay_status=1")
    pending = query_one("SELECT COUNT(*) as cnt FROM orders WHERE order_status=1 AND pay_status=1")
    total = query_one("SELECT COUNT(*) as cnt, IFNULL(SUM(amount),0) as total FROM orders WHERE pay_status=1")
    return jsonify({'code': 0, 'data': {'today_count': today['cnt'], 'today_amount': float(today['total']), 'pending_count': pending['cnt'], 'total_count': total['cnt'], 'total_amount': float(total['total'])}})

@admin_bp.route('/admin/orders')
@login_required
def get_orders():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    status = request.args.get('status', '')
    pay_st = request.args.get('pay_status', '')
    keyword = request.args.get('keyword', '')
    offset = (page - 1) * page_size
    where = ['1=1']
    params = []
    if status != '':
        where.append('order_status=%s')
        params.append(int(status))
    if pay_st != '':
        where.append('pay_status=%s')
        params.append(int(pay_st))
    if keyword:
        where.append('(order_no LIKE %s OR game_account LIKE %s OR product_name LIKE %s)')
        kw = '%' + keyword + '%'
        params.extend([kw, kw, kw])
    where_str = ' AND '.join(where)
    total_cnt = query_one('SELECT COUNT(*) as cnt FROM orders WHERE ' + where_str, params)['cnt']
    orders = query_all('SELECT id, order_no, product_name, game_name, game_account, game_zone, game_role, amount, pay_status, order_status, remark, admin_remark, paid_at, completed_at, created_at FROM orders WHERE ' + where_str + ' ORDER BY created_at DESC LIMIT %s OFFSET %s', params + [page_size, offset])
    def fmt(o):
        for k in ['paid_at', 'completed_at', 'created_at']:
            if o.get(k):
                o[k] = o[k].strftime('%Y-%m-%d %H:%M:%S')
        o['amount'] = float(o['amount'])
        return o
    return jsonify({'code': 0, 'data': [fmt(o) for o in orders], 'total': total_cnt, 'page': page, 'page_size': page_size})

@admin_bp.route('/admin/order/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    order = query_one('SELECT * FROM orders WHERE id=%s', (order_id,))
    if not order:
        return jsonify({'code': -1, 'msg': '订单不存在'})
    for k in ['paid_at', 'completed_at', 'created_at']:
        if order.get(k):
            order[k] = order[k].strftime('%Y-%m-%d %H:%M:%S')
    order['amount'] = float(order['amount'])
    return jsonify({'code': 0, 'data': order})

@admin_bp.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    data = request.json or {}
    order = query_one('SELECT * FROM orders WHERE id=%s', (order_id,))
    if not order:
        return jsonify({'code': -1, 'msg': '订单不存在'})
    if order['order_status'] == 2:
        return jsonify({'code': -1, 'msg': '订单已完成'})
    execute('UPDATE orders SET order_status=2, completed_at=NOW(), admin_remark=%s WHERE id=%s', (data.get('admin_remark', ''), order_id))
    try:
        updated = query_one('SELECT * FROM orders WHERE id=%s', (order_id,))
        send_order_complete_notify(order['openid'], updated)
    except:
        pass
    return jsonify({'code': 0, 'msg': '已标记完成'})

@admin_bp.route('/admin/order/<int:order_id>/refund', methods=['POST'])
@login_required
def refund_order(order_id):
    data = request.json or {}
    execute('UPDATE orders SET order_status=3, admin_remark=%s WHERE id=%s', (data.get('admin_remark', '已退款'), order_id))
    return jsonify({'code': 0, 'msg': '已标记退款'})

@admin_bp.route('/admin/products')
@login_required
def get_products():
    game_id = request.args.get('game_id', '')
    keyword = request.args.get('keyword', '')
    where = ['1=1']
    params = []
    if game_id:
        where.append('game_id=%s')
        params.append(game_id)
    if keyword:
        where.append('(name LIKE %s OR game_name LIKE %s)')
        kw = '%' + keyword + '%'
        params.extend([kw, kw])
    where_str = ' AND '.join(where)
    if params:
        products = query_all('SELECT * FROM products WHERE ' + where_str + ' ORDER BY sort_order, id', params)
    else:
        products = query_all('SELECT * FROM products ORDER BY sort_order, id')
    for p in products:
        p['price'] = float(p['price'])
        p['cost'] = float(p['cost']) if p['cost'] else None
        p['created_at'] = p['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': products})

@admin_bp.route('/admin/product', methods=['POST'])
@login_required
def add_product():
    d = request.json
    execute('INSERT INTO products (game_id, game_name, name, price, cost, description, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (d.get('game_id'), d.get('game_name', ''), d['name'], d['price'], d.get('cost'), d.get('description', ''), d.get('sort_order', 0)))
    return jsonify({'code': 0, 'msg': '添加成功'})

@admin_bp.route('/admin/product/<int:pid>', methods=['PUT'])
@login_required
def update_product(pid):
    d = request.json
    execute('UPDATE products SET game_id=%s, game_name=%s, name=%s, price=%s, cost=%s, description=%s, is_active=%s, sort_order=%s WHERE id=%s',
        (d.get('game_id'), d.get('game_name', ''), d['name'], d['price'], d.get('cost'), d.get('description', ''), d.get('is_active', 1), d.get('sort_order', 0), pid))
    return jsonify({'code': 0, 'msg': '更新成功'})

@admin_bp.route('/admin/product/<int:pid>', methods=['DELETE'])
@login_required
def delete_product(pid):
    execute('UPDATE products SET is_active=0 WHERE id=%s', (pid,))
    return jsonify({'code': 0, 'msg': '已下架'})

@admin_bp.route('/admin/games')
@login_required
def admin_games():
    games = query_all('SELECT g.*, c.name as category_name FROM games g LEFT JOIN categories c ON c.id=g.category_id ORDER BY g.sort_order')
    for g in games:
        g['created_at'] = g['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': games})

@admin_bp.route('/admin/game', methods=['POST'])
@login_required
def add_game():
    d = request.json
    execute('INSERT INTO games (category_id, name, icon, icon_url, cover_color, description, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (d['category_id'], d['name'], d.get('icon', '🎮'), d.get('icon_url'), d.get('cover_color', '#1a1a2e'), d.get('description', ''), d.get('sort_order', 0)))
    return jsonify({'code': 0, 'msg': '添加成功'})

@admin_bp.route('/admin/game/<int:gid>', methods=['PUT'])
@login_required
def update_game(gid):
    d = request.json
    execute('UPDATE games SET category_id=%s, name=%s, icon=%s, icon_url=%s, cover_color=%s, description=%s, sort_order=%s, is_active=%s WHERE id=%s',
        (d['category_id'], d['name'], d.get('icon', '🎮'), d.get('icon_url'), d.get('cover_color', '#1a1a2e'), d.get('description', ''), d.get('sort_order', 0), d.get('is_active', 1), gid))
    return jsonify({'code': 0, 'msg': '更新成功'})

@admin_bp.route('/admin/game/<int:gid>', methods=['DELETE'])
@login_required
def delete_game(gid):
    execute('UPDATE games SET is_active=0 WHERE id=%s', (gid,))
    return jsonify({'code': 0, 'msg': '已删除'})

@admin_bp.route('/admin/categories')
@login_required
def admin_categories():
    cats = query_all('SELECT * FROM categories ORDER BY sort_order')
    for c in cats:
        c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': cats})

@admin_bp.route('/admin/category', methods=['POST'])
@login_required
def add_category():
    d = request.json
    execute('INSERT INTO categories (name, icon, sort_order) VALUES (%s,%s,%s)', (d['name'], d.get('icon', '🎮'), d.get('sort_order', 0)))
    return jsonify({'code': 0, 'msg': '添加成功'})

@admin_bp.route('/admin/category/<int:cid>', methods=['PUT'])
@login_required
def update_category(cid):
    d = request.json
    execute('UPDATE categories SET name=%s, icon=%s, sort_order=%s, is_active=%s WHERE id=%s', (d['name'], d.get('icon', '🎮'), d.get('sort_order', 0), d.get('is_active', 1), cid))
    return jsonify({'code': 0, 'msg': '更新成功'})

@admin_bp.route('/admin/category/<int:cid>', methods=['DELETE'])
@login_required
def delete_category(cid):
    execute('UPDATE categories SET is_active=0 WHERE id=%s', (cid,))
    return jsonify({'code': 0, 'msg': '已删除'})

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@admin_bp.route('/admin/upload/game_icon', methods=['POST'])
@login_required
def upload_game_icon():
    if 'file' not in request.files:
        return jsonify({'code': -1, 'msg': '没有收到文件'})
    f = request.files['file']
    if f.filename == '':
        return jsonify({'code': -1, 'msg': '未选择文件'})
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'code': -1, 'msg': '只支持 PNG/JPG/GIF/WEBP 格式'})
    filename = uuid.uuid4().hex + '.' + ext
    save_dir = '/root/wechat_recharge/static/uploads/games'
    os.makedirs(save_dir, exist_ok=True)
    f.save(os.path.join(save_dir, filename))
    return jsonify({'code': 0, 'url': '/static/uploads/games/' + filename})


# ── 服务器类型管理 ──

@admin_bp.route('/admin/game/<int:game_id>/servers')
@login_required
def get_servers(game_id):
    servers = query_all(
        "SELECT * FROM game_servers WHERE game_id=%s ORDER BY sort_order",
        (game_id,)
    )
    for s in servers:
        s['created_at'] = s['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': servers})

@admin_bp.route('/admin/server', methods=['POST'])
@login_required
def add_server():
    d = request.json
    execute(
        "INSERT INTO game_servers (game_id, name, sort_order) VALUES (%s,%s,%s)",
        (d['game_id'], d['name'], d.get('sort_order', 0))
    )
    return jsonify({'code': 0, 'msg': '添加成功'})

@admin_bp.route('/admin/server/<int:sid>', methods=['PUT'])
@login_required
def update_server(sid):
    d = request.json
    execute(
        "UPDATE game_servers SET name=%s, sort_order=%s, is_active=%s WHERE id=%s",
        (d['name'], d.get('sort_order', 0), d.get('is_active', 1), sid)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})

@admin_bp.route('/admin/server/<int:sid>', methods=['DELETE'])
@login_required
def delete_server(sid):
    execute("UPDATE game_servers SET is_active=0 WHERE id=%s", (sid,))
    return jsonify({'code': 0, 'msg': '已删除'})

# ── 商品种类管理 ──

@admin_bp.route('/admin/server/<int:server_id>/types')
@login_required
def get_types(server_id):
    types = query_all(
        "SELECT * FROM product_types WHERE server_id=%s ORDER BY sort_order",
        (server_id,)
    )
    for t in types:
        t['created_at'] = t['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': types})

@admin_bp.route('/admin/type', methods=['POST'])
@login_required
def add_type():
    d = request.json
    execute(
        "INSERT INTO product_types (server_id, game_id, name, sort_order) VALUES (%s,%s,%s,%s)",
        (d['server_id'], d['game_id'], d['name'], d.get('sort_order', 0))
    )
    return jsonify({'code': 0, 'msg': '添加成功'})

@admin_bp.route('/admin/type/<int:tid>', methods=['PUT'])
@login_required
def update_type(tid):
    d = request.json
    execute(
        "UPDATE product_types SET name=%s, sort_order=%s, is_active=%s WHERE id=%s",
        (d['name'], d.get('sort_order', 0), d.get('is_active', 1), tid)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})

@admin_bp.route('/admin/type/<int:tid>', methods=['DELETE'])
@login_required
def delete_type(tid):
    execute("UPDATE product_types SET is_active=0 WHERE id=%s", (tid,))
    return jsonify({'code': 0, 'msg': '已删除'})
