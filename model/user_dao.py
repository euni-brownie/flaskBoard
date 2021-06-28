from sqlalchemy import text
import connection as dbconn
import pandas as pd
from flask import request, jsonify
import datetime

# from html.parser import HTMLParser
import html


def check_exist_id(request):
    data = request.get_json()
    user_id = data["userId"]

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("SELECT * FROM USER WHERE userId = :user_id")

        result = conn.execute(query, user_id=user_id)
    existed = True if result.rowcount > 0 else False
    return jsonify(existed=existed)


def create_user(request):
    user = {
        "user_id": request.form["user_id"],
        "user_name": request.form["user_name"],
        "user_password": request.form["user_password"],
        "user_email": request.form["user_email"],
    }
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "INSERT INTO USER(userId,name,password,email) VALUES(:user_id, :user_name, :user_password, :user_email)"
        )
        result = conn.execute(
            query,
            user_id=user["user_id"],
            user_name=user["user_name"],
            user_password=user["user_password"],
            user_email=user["user_email"],
        )
        is_successed = True if result.rowcount == 1 else False
    return is_successed


def get_user_by_id(request):
    target_user = {
        "user_id": request.form["user_id"],
        "user_password": request.form["user_password"],
    }
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("SELECT * FROM USER WHERE userId = :user_id")
        result = conn.execute(query, user_id=target_user["user_id"])
    df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    user = df_result.to_dict("records")
    return user
