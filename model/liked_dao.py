from sqlalchemy import text
import connection as dbconn
import pandas as pd
from flask import Flask, request, jsonify, session
import datetime

# from html.parser import HTMLParser
import html
from werkzeug.utils import secure_filename
import os
import platform
import paging


def check_exist_liked(request):
    data = request.get_json()
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "INSERT INTO LIKED(userId, articleIdx) VALUES (:userId, :articleIdx)"
        )
        result = conn.execute(
            query,
            userId=session.get("userId"),
            articleIdx=data["article_idx"],
        )
        success = True if result.rowcount == 1 else False

    return jsonify(success=success)

# check_exist_liked


def add_liked_for_article_by_user(request):
    data = request.get_json()
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "SELECT count(*) as count FROM LIKED WHERE userid LIKE :userId AND articleIdx = :articleIdx"
        )
        result = conn.execute(
            query,
            userId=session.get("userId"),
            articleIdx=data["article_idx"],
        )
        df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
        count = df_result.to_dict("records")
        success = True if count[0]['count'] > 0 else False

    return jsonify(success=success)


def create_comment(request):
    data = request.get_json()
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "INSERT INTO COMMENT(content, userId, articleIdx) VALUES (:content, :userId, :articleIdx)"
        )
        result = conn.execute(
            query,
            content=data["comment_content"],
            userId=session.get("userId"),
            articleIdx=data["article_idx"],
        )
        success = True if result.rowcount == 1 else False

    return jsonify(success=success)


def get_comment_list(request):
    article_idx = request.args.get("articleIdx")
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text(
            "SELECT c.commentIdx AS commentIdx, c.content AS content, c.userId AS userId, u.name AS name, c.articleIdx as articleIdx, c.regDate AS regDate FROM COMMENT c, USER u WHERE c.userId = u.userId AND c.articleIdx = :articleIdx ORDER BY regDate desc"
        )
        result = conn.execute(
            query,
            articleIdx=article_idx,
        )
        df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    comment_list = df_result.to_dict("records")
    return comment_list


def delete_comment(request):
    data = request.get_json()
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM COMMENT WHERE commentIdx = :commentIdx")
        result = conn.execute(query, commentIdx=data["comment_idx"])
        success = True if result.rowcount == 1 else False

    return jsonify(success=success)
