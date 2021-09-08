from flask import (
    Flask,
    request,
    render_template,
    url_for,
    redirect,
    session,
    jsonify,
    flash,
)
from flask.globals import session
from flask.helpers import make_response
from flask.json import jsonify
from flask.wrappers import Response
from sqlalchemy.sql.expression import false
import model.article_dao as article_dao
import model.comment_dao as comment_dao
import model.user_dao as user_dao
import model.file_dao as file_dao
import model.rememberme_dao as rememberme_dao
import json
from decorator import login_required
from common import generate_random_slug_code
from flask_wtf import Form
from form import RegisterForm
from urllib.parse import urlparse
from common import UserAgentParser
from datetime import datetime, timedelta
from flask_mail import Mail, Message

application = Flask(__name__)  # WSGI 실행 환경에 맞춰서 app 변수명 변경
application.jinja_env.trim_blocks = True
application.config["JSON_AS_ASCII"] = False  # json한글 처리 설정
application.config["MAX_CONTENT_LENGTH"] = 1024 * \
    1024 * 10 + 1  # 10MB 넘을 수 없도록 설정
application.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".gif"]
application.config["UPLOAD_PATH"] = "uploads"
application.config["MAIL_SERVER"] = "smtp.gmail.com"
application.config["MAIL_PORT"] = 465
application.config["MAIL_USERNAME"] = "jeongeun.kim@ptbwa.com"
application.config["MAIL_PASSWORD"] = "Ptbw@917#!"
application.config["MAIL_USE_TLS"] = False
application.config["MAIL_USE_SSL"] = True
mail = Mail(application)


@application.route("/")
def _hello():
    return "Hello, World!"


@application.route("/login", methods=["GET", "POST"])
def _login():
    if request.method == "GET":
        url = urlparse(request.referrer)
        referrer = (
            request.referrer.split(url.netloc)[
                1] if request.referrer else "/main"
        )
        if referrer is not None:
            if referrer == "/login" or referrer == "/join":
                session["referrer"] = "/main"
            else:
                session["referrer"] = referrer

        # 이미 로그인 했을 때
        if session.get("logined") is not None:
            return redirect(session.get("referrer"))
            # return redirect(url_for("_main"))
        else:
            # auto login already checked
            if request.cookies.get("rememberme"):
                # dp updated
                rememberme_dao.update_expire_date(request)
                response = make_response(redirect(url_for("_main")))
                # 쿠키 expire 연장
                response.set_cookie(
                    "rememberme", expires=datetime.now() + timedelta(days=30)
                )
                return response
            else:
                return render_template("login.html")
    else:
        user = user_dao.get_user_by_id(request)
        if len(user) != 0:
            if str(request.form["user_password"]) == user[0]["password"]:

                # 공통
                session["logined"] = True
                session["userIdx"] = user[0]["userIdx"]
                session["userId"] = user[0]["userId"]
                session["name"] = user[0]["name"]
                response = jsonify(
                    result_msg="SUCCESS", referrer=session.get("referrer")
                )
                # if 자동로그인 체크
                is_successed = false
                key = ""
                if request.form.get("autologin") == "on":
                    is_successed, key = rememberme_dao.create_key(request)
                    response.set_cookie(
                        "rememberme",
                        value=key,
                        expires=datetime.now() + timedelta(days=30),
                        path="/",
                    )

                return response
            else:
                return jsonify(result_msg="PW_NOT_COR")
        return jsonify(result_msg="ID_ERR")


@application.route("/logout")
@login_required
def _logout():
    session.clear()
    if request.cookies.get("rememberme"):
        rememberme_dao.delete_key(request)
        response = make_response(redirect(url_for("_login")))
        response.set_cookie("rememberme", expires=0)
        return response
    else:
        return redirect(url_for("_main"))


@application.route("/join")
def _join():
    form = RegisterForm()
    return render_template("join.html", form=form)


@application.route("/join/user", methods=["POST"])
def _join_user():
    print(request.form)
    form = RegisterForm()
    error_list = []
    if form.validate_on_submit() == False:  # 아이디 중복 검사 및 인증번호 확인도 하기
        for errorMessages in form.errors.items():
            for err in errorMessages:
                error_list.append(err)
        return jsonify(error=error_list)

    if session.get("certified") == None or False:
        error_list.append("EMAIL_ERROR")
        error_list.append("이메일 인증을 실패했습니다. 다시 확인해주세요.")
        return jsonify(error=error_list)

    session.pop("certified", None)
    session.pop("auth_code", None)
    session.pop("auth_date", None)
    successed = user_dao.create_user(request)
    return jsonify(successed=successed)


@application.route("/main")
def _main():
    article_list, paging_value, current_index, filter, keyword = article_dao.get_list()
    return render_template(
        "main.html",
        article_list=article_list,
        paging_value=paging_value,
        current_index=current_index,
        filter=filter,
        keyword=keyword,
    )


@application.route("/write")
@login_required
def _write():
    return render_template("write.html")


@application.route("/edit")
@login_required
def _edit():
    article = article_dao.get_article(request)
    if session["userId"] != article[0]["userId"]:
        return redirect(url_for("_main"))
    else:
        return render_template("edit.html", article=article)


@application.route("/reply")
@login_required
def _reply():
    article = article_dao.get_article(request)
    return render_template("reply.html", article=article)


@application.route("/article")
@login_required
def _article():
    article = article_dao.get_article(request)
    comments = comment_dao.get_comment_list(request)
    same_user = True if (session["userId"] == article[0]["userId"]) else False
    print("#same_user : ", same_user)
    return render_template(
        "article.html", article=article, same_user=same_user, comments=comments
    )


@application.route("/create", methods=["POST"])
@login_required
def _create():
    is_successed = article_dao.create_article(request)
    return redirect(url_for("_main", created=is_successed))


@application.route("/update", methods=["POST"])
@login_required
def _update():
    article_idx, is_successed = article_dao.update_article(request)
    if is_successed:
        return redirect(
            url_for("_article", articleIdx=article_idx, updated=is_successed)
        )
    else:
        return redirect(url_for("_edit", articleIdx=article_idx, updated=is_successed))


@application.route("/create/reply", methods=["POST"])
@login_required
def _create_reply():
    is_successed = article_dao.reply_article(request)
    return redirect(url_for("_main", created=is_successed))


@application.route("/delete")
@login_required
def _delete():
    article = article_dao.get_article(request)

    if session["userId"] != article[0]["userId"]:
        return redirect(url_for("_main"))
    else:
        article_success = article_dao.delete_article(request)
        file_success = file_dao.delete_file(request)
        return redirect(url_for("_main", deleted=(article_success and file_success)))


@application.route("/check/password", methods=["POST"])
def _check_password():
    return article_dao.check_password(request)


@application.route("/check/exist/id", methods=["POST"])
def _check_exist_id():
    return user_dao.check_exist_id(request)


@application.route("/check/authcode", methods=["POST"])
def _check_authcode():
    result_message = ""
    data = request.get_json()
    user_auth_code = data["user_auth_code"]
    if session.get("auth_code") == user_auth_code:
        if session.get("auth_date") > datetime.now():
            session["certified"] = True
            result_message = "success"
        else:
            session["certified"] = False
            result_message = "시간을 초과했습니다. 재전송 후 다시 인증해주세요."
    else:
        session["certified"] = False
        result_message = "인증번호가 일치하지 않습니다. 다시 입력해주세요."

    return jsonify(result=result_message)


@application.route("/file/download")
@login_required
def _file_download():
    return file_dao.file_download(request)


@application.route("/send/authmail", methods=["POST"])
def _send_authmail():
    session["auth_code"] = generate_random_slug_code(length=6)
    session["auth_date"] = datetime.now() + timedelta(seconds=180)

    data = request.get_json()
    user_email = data["userEmail"]
    msg = Message(
        "[김정은님의게시판] 인증번호 확인", sender="jeongeun.kim@ptbwa.com", recipients=[user_email]
    )
    msg.html = f"""
                    <!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN' 'http://www.w3.org/TR/html4/loose.dtd'>
                    <html>
                        <head>
                            <meta charset='utf-8'>
                            <meta http-equiv='X-UA-Compatible' content='IE=edge'>
                            <meta name='viewport' content='width=device-width, initial-scale=1, maximun-scale=1, user-scalable=no'>
                            <link href='https://fonts.googleapis.com/css?family=Dosis:300|Nanum+Gothic:400,700,800'' rel='stylesheet'>
                            <title></title>
                        </head>
                        <body>
                            <table cellpadding=0 cellspacing=0 border=0 width=100% height=100% style='font-family: Nanum Gothic, sans-serif;font-size:14px;color:#161616;'>
                                <tr>
                                <td style='height:100px;border-bottom:2px solid black;text-align:center;vertical-align: bottom;padding-bottom:10px;'><img src='" + logoImgUrl + "' alt='게시판 로고 이미지'></td>
                                </tr>
                                <tr><td style='height:40px;'>&nbsp;</td></tr>
                                <tr>
                                <td style='padding-left: 30px;line-height: 170%;'>
                                    안녕하세요 김정은님의 게시판입니다.<br><br>

                                    회원가입을 위해 이메일 주소 인증을 요청하셨습니다.<br>
                                    본인이 요청한 내용이 아닐경우 본 메일을 삭제해주시기 바랍니다.<br><br>
                                </td>
                                </tr>
                                <tr>
                                <td style='padding-left: 30px;padding-right: 30px; font-weight: bold;'>
                                    <p style='padding:20px;background:#f6f6f6; '>
                                    이메일계정<br><br>
                                        {user_email}
                                    </p><br>
                                </td>
                                </tr>
                                <tr>
                                <td style='padding-left: 30px;padding-right: 30px;line-height: 170%;'>
                                    아래의 [ 인증번호 ]를 입력하여 인증을 완료하시면, 해당 서비스를 이용하실 수 있습니다.<br>
                                    (본 메일은 수신 후 3분간 유효하며, 3분이 지난경우 인증메일을 다시 요청하셔야 합니다 )<br><br>
                                </td>
                                </tr>
                                <tr>
                                <td style='text-align:center;'>
                                    <button style=" background-color: #555555;border: none;color: white;padding: 15px 32px;text-align: center;text-decoration: none;display: inline-block;font-size: 16px;margin: 4px 2px;" alt='이메일 인증 버튼'>
                                    {session.get("auth_code")}
                                </td><br><br><br><br>
                                </tr>
                                <tr><td></td></tr>
                            </table>
                        </body>
                    </html>
               """
    mail.send(msg)
    success = "success"
    return jsonify(success=success)


@application.route("/create/comment", methods=["POST"])
def _create_comment():
    return comment_dao.create_comment(request)


@application.route("/get/comment", methods=["POST"])
def _get_comment():
    return comment_dao.get_comment_list(request)


@application.route("/delete/comment", methods=["POST"])
def _delete_comment():
    return comment_dao.delete_comment(request)


@application.route("/method", methods=["GET", "POST"])
def method():
    if request.method == "GET":
        return "GET으로 전달"

    else:
        return "POST로 전달"


if __name__ == "__main__":
    application.secret_key = "20210524"
    application.run(host="0.0.0.0", debug=True, port=5555)  # 모든 IP 방식 접속 허용
