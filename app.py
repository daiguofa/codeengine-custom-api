from flask import Flask, request, jsonify
import sqlite3
import os
import threading

app = Flask(__name__)

# 数据库锁（防止多线程冲突）
db_lock = threading.Lock()

# ==============================
# 数据库初始化（自动创建，永久存在）
# 存储路径：/tmp（Code Engine 唯一可写目录）
# ==============================
def init_database():
    DB_PATH = "/tmp/insurance.db"

    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 客户表（用于身份验证）
        c.execute('''CREATE TABLE IF NOT EXISTS customers (
            name TEXT PRIMARY KEY,
            customer_id TEXT,
            policies TEXT
        )''')

        # 理赔表
        c.execute('''CREATE TABLE IF NOT EXISTS claims (
            claim_number TEXT PRIMARY KEY,
            customer_name TEXT,
            accident_info TEXT,
            status TEXT
        )''')

        # 插入测试客户（可验证用户名）
        test_customers = [
            ("张三", "CUST_2025001", "车辆保险,交强险"),
            ("李四", "CUST_2025002", "商业险,交强险"),
            ("王五", "CUST_2025003", "全车保险,第三者责任险")
        ]

        for name, cid, policies in test_customers:
            c.execute('''INSERT OR IGNORE INTO customers VALUES (?, ?, ?)''',
                      (name, cid, policies))

        conn.commit()
        conn.close()

# 服务启动时自动初始化数据库
init_database()

# ==============================
# 1. 客户身份验证（真实查询SQLite）
# ==============================
@app.route("/verify_customer_identity", methods=["POST"])
def verify_customer():
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"status": "failed", "message": "请输入姓名"}), 400

    try:
        with db_lock:
            conn = sqlite3.connect("/tmp/insurance.db")
            c = conn.cursor()
            c.execute("SELECT * FROM customers WHERE name = ?", (name,))
            user = c.fetchone()
            conn.close()

        if user:
            return jsonify({
                "status": "success",
                "message": f"客户 {name} 身份验证成功",
                "customer_id": user[1],
                "policies": user[2].split(",")
            })
        else:
            return jsonify({"status": "failed", "message": "客户不存在"}), 401

    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

# ==============================
# 2. 创建理赔报案
# ==============================
@app.route("/create_claim_request", methods=["POST"])
def create_claim():
    data = request.get_json()
    name = data.get("name", "").strip()
    accident = data.get("accident_info", "无事故信息")

    if not name:
        return jsonify({"status": "failed", "message": "请先验证身份"}), 400

    claim_id = f"CLAIM_{os.urandom(3).hex().upper()}"

    try:
        with db_lock:
            conn = sqlite3.connect("/tmp/insurance.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO claims VALUES (?, ?, ?, ?)",
                (claim_id, name, accident, "处理中")
            )
            conn.commit()
            conn.close()

        return jsonify({
            "status": "success",
            "claim_number": claim_id,
            "message": "理赔已创建"
        })

    except Exception as e:
        return jsonify({"status": "failed", "reason": str(e)}), 500

# ==============================
# 3. 查询理赔状态
# ==============================
@app.route("/check_claim_status", methods=["POST"])
def check_claim():
    data = request.get_json()
    claim_no = data.get("claim_number", "").strip()

    if not claim_no:
        return jsonify({"status": "failed", "message": "请输入理赔号"}), 400

    try:
        with db_lock:
            conn = sqlite3.connect("/tmp/insurance.db")
            c = conn.cursor()
            c.execute("SELECT * FROM claims WHERE claim_number = ?", (claim_no,))
            res = c.fetchone()
            conn.close()

        if res:
            return jsonify({
                "claim_number": res[0],
                "customer_name": res[1],
                "accident_info": res[2],
                "status": res[3]
            })
        else:
            return jsonify({"status": "not_found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

# ==============================
# 健康检查
# ==============================
@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "database": "SQLite 内置",
        "mode": "POC 保险理赔服务"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
