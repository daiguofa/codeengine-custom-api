from flask import Flask, request, jsonify
import sqlite3
import os
import threading

app = Flask(__name__)
db_lock = threading.Lock()

# ==========================
# 初始化数据库（含车辆信息）
# ==========================
def init_database():
    DB_PATH = "/tmp/insurance.db"

    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 客户表
        c.execute('''CREATE TABLE IF NOT EXISTS customers (
            name TEXT PRIMARY KEY,
            customer_id TEXT,
            policies TEXT
        )''')

        # 车辆表（你文档要求的字段）
        c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
            name TEXT,
            plate TEXT,
            brand TEXT,
            model TEXT,
            color TEXT,
            vin TEXT
        )''')

        # 理赔表
        c.execute('''CREATE TABLE IF NOT EXISTS claims (
            claim_number TEXT PRIMARY KEY,
            name TEXT,
            accident_info TEXT,
            status TEXT
        )''')

        # 测试客户
        customers = [
            ("张三", "CUST_2025001", "车辆保险,交强险"),
            ("李四", "CUST_2025002", "商业险,交强险"),
            ("王五", "CUST_2025003", "全车保险,三者险")
        ]
        for i in customers:
            c.execute("INSERT OR IGNORE INTO customers VALUES (?,?,?)", i)

        # ======================
        # 🔥 车辆数据（补齐完成）
        # ======================
        vehicles = [
            ("张三", "京A12345", "Toyota", "Camry", "黑色", "LFMAP86CXXX001"),
            ("李四", "沪B67890", "Honda", "Civic", "白色", "LFMAP86CXXX002"),
            ("王五", "粤C98765", "VW", "Passat", "灰色", "LFMAP86CXXX003")
        ]
        for v in vehicles:
            c.execute("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?)", v)

        conn.commit()
        conn.close()

init_database()

# ==========================
# 1 身份验证 + 返回车辆信息
# ==========================
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
            c.execute("SELECT * FROM customers WHERE name=?", (name,))
            user = c.fetchone()

            if not user:
                conn.close()
                return jsonify({"status": "failed", "message": "客户不存在"}), 401

            # 查询车辆
            c.execute("SELECT * FROM vehicles WHERE name=?", (name,))
            car = c.fetchone()
            conn.close()

        return jsonify({
            "status": "success",
            "customer_id": user[1],
            "name": user[0],
            "policies": user[2].split(","),
            "vehicle": {
                "plate": car[1],
                "brand": car[2],
                "model": car[3],
                "color": car[4],
                "vin": car[5]
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

# ==========================
# 2 创建理赔
# ==========================
@app.route("/create_claim_request", methods=["POST"])
def create_claim():
    data = request.get_json()
    name = data.get("name", "").strip()
    accident_info = data.get("accident_info", "")

    if not name:
        return jsonify({"status": "failed", "message": "请先验证身份"}), 400

    claim_id = f"CLAIM_{os.urandom(3).hex().upper()}"

    try:
        with db_lock:
            conn = sqlite3.connect("/tmp/insurance.db")
            c = conn.cursor()
            c.execute("INSERT INTO claims VALUES (?,?,?,?)",
                      (claim_id, name, accident_info, "处理中"))
            conn.commit()
            conn.close()

        return jsonify({
            "status": "success",
            "claim_number": claim_id,
            "message": "理赔已创建"
        })
    except:
        return jsonify({"status": "failed"}), 500

# ==========================
# 3 查询理赔状态
# ==========================
@app.route("/check_claim_status", methods=["POST"])
def check_claim():
    data = request.get_json()
    claim_no = data.get("claim_number", "").strip()

    try:
        with db_lock:
            conn = sqlite3.connect("/tmp/insurance.db")
            c = conn.cursor()
            c.execute("SELECT * FROM claims WHERE claim_number=?", (claim_no,))
            res = c.fetchone()
            conn.close()

        if res:
            return jsonify({
                "claim_number": res[0],
                "status": res[3],
                "accident": res[2]
            })
        else:
            return jsonify({"status": "not_found"}), 404
    except:
        return jsonify({"status": "error"}), 500

# ==========================
# 查看所有客户（调试）
# ==========================
@app.route("/list_customers", methods=["GET"])
def list_customers():
    with db_lock:
        conn = sqlite3.connect("/tmp/insurance.db")
        c = conn.cursor()
        c.execute("SELECT * FROM customers")
        customers = c.fetchall()
        c.execute("SELECT * FROM vehicles")
        vehicles = c.fetchall()
        conn.close()

    return jsonify({
        "customers": customers,
        "vehicles": vehicles
    })

@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "db": "SQLite",
        "feature": "保险理赔POC完整版"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
