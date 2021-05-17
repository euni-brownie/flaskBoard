from flask import Flask, request, render_template, url_for, redirect
import model.article_dao as article_dao
import json
application = Flask(__name__)  # WSGI 실행 환경에 맞춰서 app 변수명 변경
application.jinja_env.trim_blocks = True
application.config['JSON_AS_ASCII'] = False  # json한글 처리 설정


@application.route('/')
def _hello():
    return 'Hello, World!'


@application.route('/login')
def _hellohtml():
    return render_template("login.html")


@application.route('/main')
def _main():
    article_list = article_dao.get_list()
    return render_template("main.html", article_list=article_list)


@application.route('/write')
def _write():
    return render_template("write.html")


@application.route('/edit')
def _edit():
    article = article_dao.get_article(request)
    return render_template("edit.html", article=article)


@application.route('/article')
def _article():
    article = article_dao.get_article(request)
    return render_template("article.html", article=article)


@application.route('/create', methods=['POST'])
def _create():
    is_successed = article_dao.create_article(request)
    return redirect(url_for('_main', created=is_successed))


@application.route('/update', methods=['POST'])
def _update():
    article_idx, is_successed = article_dao.update_article(request)
    if (is_successed):
        return redirect(url_for('_article', articleIdx=article_idx, updated=is_successed))
    else:
        return redirect(url_for('_edit', articleIdx=article_idx, updated=is_successed))


@ application.route('/delete')
def _delete():
    is_successed = article_dao.delete_article(request)
    return redirect(url_for('_main', deleted=is_successed))


@ application.route('/method', methods=['GET', 'POST'])
def method():
    if request.method == 'GET':
        return "GET으로 전달"
    else:
        return "POST로 전달"


if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True, port=5555)  # 모든 IP 방식 접속 허용
