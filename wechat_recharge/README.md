# 微信公众号游戏代充平台

## 项目结构
```
wechat_recharge/
├── app.py                  # 主程序入口
├── config.py               # 配置文件（填入你的密钥）
├── requirements.txt        # 依赖包
├── database.sql            # 数据库初始化SQL
├── routes/
│   ├── __init__.py
│   ├── wechat.py           # 微信公众号消息处理
│   ├── pay.py              # 微信支付
│   └── admin.py            # 管理后台API
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── order.py
│   └── product.py
├── utils/
│   ├── __init__.py
│   ├── wechat_api.py       # 微信API工具
│   └── pay_api.py          # 支付工具
└── templates/
    └── admin/
        └── index.html      # 管理后台页面
```

## 部署步骤

### 1. 安装依赖
```bash
sudo apt update
sudo apt install python3-pip python3-venv mysql-server nginx -y

cd /var/www/wechat_recharge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
mysql -u root -p
source /var/www/wechat_recharge/database.sql
```

### 3. 修改配置
编辑 `config.py`，填入你的：
- 微信公众号 AppID / AppSecret
- 微信支付商户号 / 密钥
- 数据库密码
- 管理后台密码

### 4. SSL证书（必须）
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d 你的域名
```

### 5. Nginx配置
```nginx
server {
    listen 443 ssl;
    server_name 你的域名;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6. 启动服务
```bash
# 测试运行
python app.py

# 正式运行（后台）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon
```

### 7. 微信公众号配置
在微信公众平台后台：
- 服务器地址：https://你的域名/wechat
- Token：与 config.py 中的 WECHAT_TOKEN 一致
- 消息加解密：明文模式即可

### 8. 微信支付配置
- 支付授权目录：https://你的域名/pay/
- 回调地址：https://你的域名/pay/notify
