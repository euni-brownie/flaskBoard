from sqlalchemy import text
import connection as dbconn
import pandas as pd
from flask import request, jsonify
import datetime
from common import UserAgentParser, generate_random_slug_code


def check_exist_key(request):
    key = request.cookies.get("rememberme")
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("SELECT * FROM REMEMBERME where `key` = :key")
        result = conn.execute(query, key=key)
    existed = True if result.rowcount > 0 else False
    return jsonify(existed=existed)


def create_key(request):
    userAgentParser = UserAgentParser()
    ua_str = request.headers.get("User-Agent")
    browser, os, device = userAgentParser.get_3layers(ua_str)
    user_id = request.form["user_id"]
    key = generate_random_slug_code()

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "INSERT INTO REMEMBERME(`key`,`userId`, `browser`, `os`, `time`) VALUES(:key, :user_id, :browser, :os, DATE_ADD(NOW(), INTERVAL 30 DAY))"
        )
        result = conn.execute(query, key=key, user_id=user_id, browser=browser, os=os)
        is_successed = True if result.rowcount == 1 else False
    return is_successed, key


def update_expire_date(request):
    key = request.cookies.get("rememberme")
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "UPDATE REMEMBERME SET time = DATE_ADD(NOW(), INTERVAL 30 DAY) WHERE `key` LIKE :key"
        )
        result = conn.execute(query, key=key)
        is_successed = True if result.rowcount == 1 else False
    return is_successed


def delete_key(request):
    key = request.cookies.get("rememberme")
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM REMEMBERME WHERE `key` LIKE :key")
        result = conn.execute(query, key=key)
        is_successed = True if result.rowcount == 1 else False
    return is_successed
