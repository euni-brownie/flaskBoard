from functools import wraps
from flask import request, Response, session, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("logined") is None:
            return redirect(url_for("_login"))
        else:
            return f(*args, **kwargs)

    return decorated_function
