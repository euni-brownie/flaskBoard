from sqlalchemy import text
import connection as dbconn
import pandas as pd
from flask import request, jsonify
import datetime
# from html.parser import HTMLParser
import html


def get_list():

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = f"""
                    SELECT * FROM ARTICLE
                    ORDER BY articleIdx desc;
                """
        result = conn.execute(query)
    df_result = pd.DataFrame(
        result.fetchall(), columns=result.keys())
    article_list = df_result.to_dict('records')
    print(article_list)
    return article_list


def get_article(request):
    article_idx = request.args.get('articleIdx')
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text('SELECT * FROM ARTICLE WHERE articleIdx = :article_idx;')
        result = conn.execute(query, article_idx=article_idx)
    df_result = pd.DataFrame(
        result.fetchall(), columns=result.keys())
    article = df_result.to_dict('records')

    return article


def create_article(request):
    article = {
        "article_title": request.form['article_title'],
        # "article_title": html.escape(request.form['article_title']),
        "article_author": request.form['article_author'],
        "article_content": request.form['article_content'],
        # "article_content": html.escape(request.form['article_content']),
        "article_password": request.form['article_password'],
    }
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(
            'INSERT INTO ARTICLE(userId,title,content,password) VALUES(:userId, :title, :content,:password)')
        result = conn.execute(
            query, userId=article['article_author'], title=article['article_title'], content=article['article_content'], password=article['article_password'])
        is_successed = True if result.rowcount == 1 else False
    return is_successed


def delete_article(request):
    article_idx = request.args.get('articleIdx')
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text('DELETE FROM ARTICLE WHERE articleIdx = :article_idx ;')
        result = conn.execute(query, article_idx=article_idx)
    is_successed = True if result.rowcount == 1 else False

    return is_successed


def update_article(request):
    curdate = datetime.datetime.now()
    curdate = curdate.strftime("%Y-%m-%d %H:%M")

    article = {
        "article_title": request.form['article_title'],
        # "article_title": html.escape(request.form['article_title']),
        "article_idx": request.form['article_idx'],
        "article_author": request.form['article_author'],
        "article_content": request.form['article_content'],
        # "article_content": html.escape(request.form['article_content']),
        "article_password": request.form['article_password'],
    }

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(
            'UPDATE ARTICLE SET title=:title, content=:content, updateDate=:updateDate WHERE articleIdx=:articleIdx')
        result = conn.execute(
            query, title=article['article_title'], content=article['article_content'], updateDate=curdate, articleIdx=article['article_idx'])
        print("##rowcount : ", result.rowcount)
    is_successed = True if result.rowcount == 1 else False
    return article['article_idx'], is_successed


def check_password(request):
    data = request.get_json()
    password = data['password']
    article_idx = data['articleIdx']

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(' SELECT * FROM ARTICLE WHERE articleIdx = :article_idx')
        result = conn.execute(query, article_idx=article_idx)

    df_result = pd.DataFrame(
        result.fetchall(), columns=result.keys())
    article = df_result.to_dict('records')
    correct = True if(password == article[0]['password']) else False
    return jsonify(correct=correct)
