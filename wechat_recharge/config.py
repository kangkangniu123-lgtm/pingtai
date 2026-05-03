# config.py - 所有配置都在这里修改

class Config:
    # ===== 微信公众号配置 =====
    WECHAT_APPID = "wx你的AppID"           # 公众号AppID
    WECHAT_APPSECRET = "你的AppSecret"     # 公众号AppSecret
    WECHAT_TOKEN = "你自定义的Token"        # 服务器验证Token（自己随便填一个字符串）

    # ===== 微信支付配置 =====
    MCH_ID = "你的商户号"                   # 商户号
    MCH_KEY = "你的商户API密钥"             # API密钥（32位）
    CERT_PATH = "/var/www/wechat_recharge/certs/apiclient_cert.pem"   # 证书路径
    KEY_PATH  = "/var/www/wechat_recharge/certs/apiclient_key.pem"    # 密钥路径
    NOTIFY_URL = "https://你的域名/pay/notify"   # 支付回调地址

    # ===== 数据库配置 =====
    DB_HOST = "127.0.0.1"
    DB_PORT = 3306
    DB_USER = "recharge_user"
    DB_PASS = "niuniu123"
    DB_NAME = "recharge_db"

    # ===== 管理后台配置 =====
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "niuniu123"      # 登录管理后台用
    SECRET_KEY = "abc123xyz789qwerty456poiuyt321mn" # 随便填32位字符串

    # ===== 其他配置 =====
    DEBUG = False
