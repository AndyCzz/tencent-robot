from flask import Flask, url_for
from flask_cors import CORS

app = Flask(__name__)
#设置可跨域范围
CORS(app, resources=r'/*')
    
@app.route("/")
def getI():
    return "hello"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8181)