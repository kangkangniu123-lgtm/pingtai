# routes/shop.py  —— 用户端API（商品、游戏、分类、订单查询）
from flask import Blueprint, request, jsonify, session, render_template
from utils.db import query_one, query_all, execute

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/')
@shop_bp.route('/shop')
def shop_index():
    return render_template('shop/index.html')

# ───────────────────────────────
#  公开接口（不需要登录）
# ───────────────────────────────

@shop_bp.route('/api/categories')
def get_categories():
    """获取所有分类（含每个分类下的游戏）"""
    cats = query_all(
        "SELECT id, name, icon FROM categories WHERE is_active=1 ORDER BY sort_order"
    )
    for c in cats:
        c['games'] = query_all(
            """SELECT id, name, icon, icon_url, cover_color, description
               FROM games WHERE category_id=%s AND is_active=1
               ORDER BY sort_order""",
            (c['id'],)
        )
    return jsonify({'code': 0, 'data': cats})

@shop_bp.route('/api/search')
def search_games():
    """搜索游戏"""
    kw = request.args.get('q', '').strip()
    if not kw:
        return jsonify({'code': 0, 'data': []})
    games = query_all(
        "SELECT id, name, icon, icon_url, cover_color, description FROM games WHERE name LIKE %s AND is_active=1 LIMIT 20",
        (f'%{kw}%',)
    )
    return jsonify({'code': 0, 'data': games})

@shop_bp.route('/api/game/<int:game_id>')
def get_game(game_id):
    """获取游戏详情 + 该游戏的所有档位"""
    game = query_one(
        "SELECT id, name, icon, icon_url, cover_color, description FROM games WHERE id=%s AND is_active=1",
        (game_id,)
    )
    if not game:
        return jsonify({'code': -1, 'msg': '游戏不存在'})
    products = query_all(
        """SELECT id, name, price, description FROM products
           WHERE game_id=%s AND is_active=1 ORDER BY price""",
        (game_id,)
    )
    for p in products:
        p['price'] = float(p['price'])
    game['products'] = products
    return jsonify({'code': 0, 'data': game})

@shop_bp.route('/api/hot_games')
def hot_games():
    """首页热门游戏（按订单量排序，最多8个）"""
    games = query_all(
        """SELECT g.id, g.name, g.icon, g.icon_url, g.cover_color, g.description,
                  COUNT(o.id) as order_cnt
           FROM games g
           LEFT JOIN products p ON p.game_id = g.id
           LEFT JOIN orders o ON o.product_id = p.id AND o.pay_status=1
           WHERE g.is_active=1
           GROUP BY g.id
           ORDER BY order_cnt DESC, g.sort_order
           LIMIT 8"""
    )
    return jsonify({'code': 0, 'data': games})

# ───────────────────────────────
#  需要openid的接口
# ───────────────────────────────

@shop_bp.route('/api/my_orders')
def my_orders():
    openid = session.get('openid')
    if not openid:
        return jsonify({'code': 401, 'msg': '未登录'})
    page = int(request.args.get('page', 1))
    offset = (page - 1) * 10
    orders = query_all(
        """SELECT order_no, product_name, game_name, amount,
                  pay_status, order_status, created_at, completed_at
           FROM orders WHERE openid=%s
           ORDER BY created_at DESC LIMIT 10 OFFSET %s""",
        (openid, offset)
    )
    total = query_one("SELECT COUNT(*) as cnt FROM orders WHERE openid=%s", (openid,))['cnt']
    for o in orders:
        o['amount'] = float(o['amount'])
        for k in ['created_at', 'completed_at']:
            if o.get(k):
                o[k] = o[k].strftime('%Y-%m-%d %H:%M')
    return jsonify({'code': 0, 'data': orders, 'total': total})


# ───────────────────────────────
#  管理后台：分类&游戏管理
# ───────────────────────────────

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated

# 分类
@shop_bp.route('/admin/categories')
@admin_required
def admin_categories():
    cats = query_all("SELECT * FROM categories ORDER BY sort_order")
    for c in cats:
        c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': cats})

@shop_bp.route('/admin/category', methods=['POST'])
@admin_required
def add_category():
    d = request.json
    execute(
        "INSERT INTO categories (name, icon, sort_order) VALUES (%s,%s,%s)",
        (d['name'], d.get('icon', '🎮'), d.get('sort_order', 0))
    )
    return jsonify({'code': 0, 'msg': '添加成功'})

@shop_bp.route('/admin/category/<int:cid>', methods=['PUT'])
@admin_required
def update_category(cid):
    d = request.json
    execute(
        "UPDATE categories SET name=%s, icon=%s, sort_order=%s, is_active=%s WHERE id=%s",
        (d['name'], d.get('icon','🎮'), d.get('sort_order',0), d.get('is_active',1), cid)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})

@shop_bp.route('/admin/category/<int:cid>', methods=['DELETE'])
@admin_required
def delete_category(cid):
    execute("UPDATE categories SET is_active=0 WHERE id=%s", (cid,))
    return jsonify({'code': 0, 'msg': '已删除'})

# 游戏
@shop_bp.route('/admin/games')
@admin_required
def admin_games():
    games = query_all(
        """SELECT g.*, c.name as category_name
           FROM games g LEFT JOIN categories c ON c.id=g.category_id
           ORDER BY g.sort_order"""
    )
    for g in games:
        g['created_at'] = g['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 0, 'data': games})

@shop_bp.route('/admin/game', methods=['POST'])
@admin_required
def add_game():
    d = request.json
    execute(
        "INSERT INTO games (category_id, name, icon, cover_color, description, sort_order) VALUES (%s,%s,%s,%s,%s,%s)",
        (d['category_id'], d['name'], d.get('icon','🎮'), d.get('cover_color','#1a1a2e'), d.get('description',''), d.get('sort_order',0))
    )
    return jsonify({'code': 0, 'msg': '添加成功'})

@shop_bp.route('/admin/game/<int:gid>', methods=['PUT'])
@admin_required
def update_game(gid):
    d = request.json
    execute(
        "UPDATE games SET category_id=%s, name=%s, icon=%s, cover_color=%s, description=%s, sort_order=%s, is_active=%s WHERE id=%s",
        (d['category_id'], d['name'], d.get('icon','🎮'), d.get('cover_color','#1a1a2e'), d.get('description',''), d.get('sort_order',0), d.get('is_active',1), gid)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})

@shop_bp.route('/admin/game/<int:gid>', methods=['DELETE'])
@admin_required
def delete_game(gid):
    execute("UPDATE games SET is_active=0 WHERE id=%s", (gid,))
    return jsonify({'code': 0, 'msg': '已删除'})


# ── 服务器类型和商品种类接口 ──

@shop_bp.route('/api/game/<int:game_id>/servers')
def get_game_servers(game_id):
    servers = query_all(
        "SELECT id, name, sort_order FROM game_servers WHERE game_id=%s AND is_active=1 ORDER BY sort_order",
        (game_id,)
    )
    return jsonify({'code': 0, 'data': servers})

@shop_bp.route('/api/server/<int:server_id>/types')
def get_server_types(server_id):
    types = query_all(
        "SELECT id, name, sort_order FROM product_types WHERE server_id=%s AND is_active=1 ORDER BY sort_order",
        (server_id,)
    )
    return jsonify({'code': 0, 'data': types})

@shop_bp.route('/api/type/<int:type_id>/products')
def get_type_products(type_id):
    products = query_all(
        "SELECT id, name, price, description FROM products WHERE type_id=%s AND is_active=1 ORDER BY price",
        (type_id,)
    )
    for p in products:
        p['price'] = float(p['price'])
    return jsonify({'code': 0, 'data': products})
