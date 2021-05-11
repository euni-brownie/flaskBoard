from flask import Flask, request, render_template
application = Flask(__name__)  # WSGI 실행 환경에 맞춰서 app 변수명 변경


@application.route('/')
def _hello():
    return 'Hello, World!'


@application.route('/login')
def _hellohtml():
    return render_template("login.html")


@application.route('/method', methods=['GET', 'POST'])
def method():
    if request.method == 'GET':
        return "GET으로 전달"
    else:
        return "POST로 전달"


if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True, port=5555)  # 모든 IP 방식 접속 허용
