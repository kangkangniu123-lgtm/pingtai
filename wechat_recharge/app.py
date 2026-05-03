# app.py
import os
from flask import Flask
from config import Config

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = Config.SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 最大5MB

# 确保上传目录存在
os.makedirs('static/uploads/games', exist_ok=True)

from routes.wechat import wechat_bp
from routes.pay    import pay_bp
from routes.admin  import admin_bp
from routes.shop   import shop_bp

app.register_blueprint(wechat_bp)
app.register_blueprint(pay_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(shop_bp)

@app.route('/health')
def health():
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
