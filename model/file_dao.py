import magic
from sqlalchemy import text
import connection as dbconn
from flask import Flask, request, jsonify
import os
import platform
import pandas as pd
from flask import send_file

DOWNLOAD_PATH = "euniBoard"


def get_file_list():
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = f"""
                    SELECT a.articleIdx AS articleIdx, a.userId AS userId, u.name AS name, a.title AS title, a.content AS content, a.regDate AS regDate  FROM ARTICLE a, USER u
                    WHERE a.userId LIKE u.userId
                    ORDER BY articleIdx desc;
                """
        result = conn.execute(query)
    df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    article_list = df_result.to_dict("records")
    print(article_list)
    return article_list


def file_download(request):

    file_name = request.args.get("file_name")
    file_path = request.args.get("file_path")

    mime_type = magic.from_file(file_path, mime=True)

    return send_file(
        file_path,
        attachment_filename=file_name,
        as_attachment=True,
        cache_timeout=0,
        mimetype=mime_type,
    )


def delete_file(request):
    article_idx = request.args.get("articleIdx")

    select_txt = """
                    SELECT * FROM FILE WHERE articleIdx =:article_idx
                 """
    delete_txt = """
                    DELETE FROM FILE WHERE articleIdx = :article_idx ;
                 """
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        select_result = conn.execute(text(select_txt), article_idx=article_idx)
        df_result = pd.DataFrame(select_result.fetchall(), columns=select_result.keys())
        file = df_result.to_dict("records")

        delete_result = conn.execute(text(delete_txt), article_idx=article_idx)
    is_successed = True if delete_result.rowcount == 1 else False
    os.remove(file[0]["path"])
    return is_successed
