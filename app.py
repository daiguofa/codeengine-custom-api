from flask import Flask, jsonify, request

app = Flask(__name__)

# 这就是你自己的 API 接口
@app.route('/', methods=['GET'])
def my_api():
    # 你可以在这里写任何逻辑：查询数据库、计算、返回数据
    return jsonify({
        "status": "success",
        "message": "这是我自己的 API！",
        "data": {
            "name": "我的自定义服务",
            "value": 100,
            "from": "IBM Code Engine"
        }
    })

# 第二个接口示例
@app.route('/query', methods=['GET'])
def query():
    user = request.args.get('user', 'guest')
    return jsonify({
        "user": user,
        "result": "查询成功！",
        "age": 25
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)