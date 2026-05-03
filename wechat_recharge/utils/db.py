# utils/db.py
import pymysql
from config import Config

def get_db():
    """获取数据库连接"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def query_one(sql, params=None):
    """查询单条记录"""
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        db.close()

def query_all(sql, params=None):
    """查询多条记录"""
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        db.close()

def execute(sql, params=None):
    """执行写操作（insert/update/delete）"""
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
