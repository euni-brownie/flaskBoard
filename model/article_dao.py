from sqlalchemy import text
import connection as dbconn
import pandas as pd
from flask import Flask, request, jsonify
import datetime

# from html.parser import HTMLParser
import html
from werkzeug.utils import secure_filename
import os
import platform
import paging

MAX_CONTENT_LENGTH = 1024 * 1024
UPLOAD_EXTENSIONS = [".jpg", ".png", ".gif"]
UPLOAD_PATH = "uploads"


def get_list():
    filter = str(request.args.get("filter", type=int, default=0))
    keyword = "%" + str(request.args.get("keyword", default="")) + "%"

    condition_str = (
        "and title LIKE :keyword" if (filter == "0") else "and content LIKE :keyword"
    )
    condition_str = condition_str if (keyword != "") else ""

    count_query = (
        """
                    SELECT count(*)
                    FROM 
                    (SELECT a.articleIdx AS articleIdx, a.userId AS userId, u.name AS name, a.title AS title, a.content AS content, a.regDate AS regDate 
                    FROM ARTICLE a, USER u
                    WHERE a.userId LIKE u.userId
                  """
        + condition_str
        + """
                    ) t
                    LEFT OUTER JOIN file f
                    ON t.articleIdx = f.articleIdx
                  """
    )

    # condition_str 각 쿼리에 추가하기
    select_query = (
        """
                        SELECT t.articleIdx AS articleIdx, t.userId AS userId, t.name AS name, t.title AS title, t.content AS content, t.hit AS hit, t.ref AS ref, t.indent AS indent, t.step AS step, t.regDate AS regDate , f.name AS fileName, f.path AS filePath
                        FROM 
                        (SELECT a.articleIdx AS articleIdx, a.userId AS userId, u.name AS name, a.title AS title, a.content AS content, a.regDate AS regDate , a.hit AS hit, a.ref AS ref, a.indent AS indent, a.step AS step
                        FROM ARTICLE a, USER u
                        WHERE a.userId LIKE u.userId
                    """
        + condition_str
        + """
                        ORDER BY a.ref DESC, a.step ASC
                        limit :limit_num, :page_size
                        ) t
                        LEFT OUTER JOIN file f
                        ON t.articleIdx = f.articleIdx
                   """
    )
    # condition_str 각 쿼리에 추가하기
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        # get count
        count_result = conn.execute(text(count_query), keyword=keyword)
        count_rows = count_result.fetchone()
        total_rows = count_rows[0]

        # pagination
        current_index = request.args.get("page", type=int, default=1)
        page_size = paging.DEFAULT_PAGE_SIZE
        paging_value = paging.Paging(page_size, current_index, total_rows)
        limit_num = paging_value.get_start_row()

        result = conn.execute(
            text(select_query),
            limit_num=limit_num,
            page_size=page_size,
            keyword=keyword,
        )
    df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    article_list = df_result.to_dict("records")

    print(article_list)

    keyword = keyword[1:-1]
    return article_list, paging_value, current_index, filter, keyword


def get_article(request):
    article_idx = request.args.get("articleIdx")
    query_txt = """
                    select t.articleIdx AS articleIdx, t.userId AS userId, t.name AS name, t.title AS title, t.content AS content, t.hit, t.ref, t.indent, t.step, t.regDate AS regDate, f.name AS fileName, f.path AS filePath 
                    from
                    (SELECT a.articleIdx AS articleIdx, a.userId AS userId, u.name AS name, a.title AS title, a.content AS content, a.hit, a.ref, a.indent, a.step, a.regDate AS regDate  FROM ARTICLE a, USER u WHERE a.userId LIKE u.userId AND articleIdx = :article_idx) t
                    LEFT OUTER JOIN
                    file f 
                    ON t.articleIdx = f.articleIdx;
                """

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query_txt), article_idx=article_idx)
    df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    article = df_result.to_dict("records")

    return article


def create_article(request):
    article_success = False
    file_success = True

    article = {
        "article_title": request.form["article_title"],
        "article_id": request.form["article_id"],
        "article_content": request.form["article_content"],
        "article_file": request.files["article_file"],
    }

    update_ref = """
                    UPDATE ARTICLE
                    SET ref=:articleIdx
                    WHERE articleIdx=:articleIdx
                 """

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(
            "INSERT INTO ARTICLE(userId,title,content) VALUES(:userId, :title, :content)"
        )
        article_result = conn.execute(
            query,
            userId=article["article_id"],
            title=article["article_title"],
            content=article["article_content"],
        )

        article_success = True if article_result.rowcount == 1 else False

        created_idx = conn.execute("SELECT LAST_INSERT_ID() AS id").fetchone()

        conn.execute(  # ref값 자기 자신으로 변경
            text(update_ref),
            articleIdx=created_idx["id"],
        )
        # save file

        # 한글 지원 X 주석처리
        # article['article_file'].filename = secure_filename(
        #     article['article_file'].filename)
        file_type = ""

        if article["article_file"].filename != "":
            file_type = os.path.splitext(article["article_file"].filename)[1]

            # 파일 확장자 불일치
            if file_type not in UPLOAD_EXTENSIONS:
                file_success = False
                delete_article_by_idx(created_idx["id"])
                return article_success and file_success

            os_root = "C:" if platform.system() == "Windows" else "usr"

            if not os.path.exists(os_root + os.sep + UPLOAD_PATH):
                os.makedirs(os_root + os.sep + UPLOAD_PATH)

            file_path = os.path.join(
                os.sep,
                os_root + os.sep + UPLOAD_PATH + os.sep,
                article["article_file"].filename,
            )
            article["article_file"].save(file_path)

            file_length = os.stat(file_path).st_size

            query = text(
                "INSERT INTO FILE(name,type,size, articleIdx, path) VALUES(:name, :type, :size, :articleIdx, :path)"
            )

            file_result = conn.execute(
                query,
                name=article["article_file"].filename,
                type=file_type,
                size=file_length,
                articleIdx=created_idx["id"],
                path=file_path,
            )

            file_success = True if file_result.rowcount == 1 else False

    return article_success and file_success


def delete_article(request):
    article_idx = request.args.get("articleIdx")
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM ARTICLE WHERE articleIdx = :article_idx ;")
        result = conn.execute(query, article_idx=article_idx)
    is_successed = True if result.rowcount == 1 else False

    return is_successed


def delete_article_by_idx(idx):
    article_idx = idx
    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM ARTICLE WHERE articleIdx = :article_idx ;")
        result = conn.execute(query, article_idx=article_idx)
    is_successed = True if result.rowcount == 1 else False

    return is_successed


def update_article(request):
    article_success = False
    file_success = True
    curdate = datetime.datetime.now()
    curdate = curdate.strftime("%Y-%m-%d %H:%M")

    article = {
        "article_title": request.form["article_title"],
        # "article_title": html.escape(request.form['article_title']),
        "article_idx": request.form["article_idx"],
        # "article_author": request.form['article_author'],
        "article_content": request.form["article_content"],
        # "article_content": html.escape(request.form['article_content']),
        "article_file": request.files["article_file"],
        "prev_file_name": request.form["prev_file_name"],
        "prev_file_path": request.form["prev_file_path"],
        "file_updated": request.form["file_updated"],
    }
    print("# file updated value : ", article["file_updated"])

    article_update_txt = """
                            UPDATE ARTICLE SET title=:title, content=:content, updateDate=:updateDate
                            WHERE articleIdx=:articleIdx
                         """
    file_update_txt = """
                        UPDATE FILE 
                        SET name=:name, type = :type, size = :size, path = :path
                        WHERE articleIdx=:articleIdx
                     """
    file_insert_txt = """
                       INSERT INTO FILE(name,type,size, articleIdx, path)
                       VALUES(:name, :type, :size, :articleIdx, :path)
                     """

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        result = conn.execute(
            text(article_update_txt),
            title=article["article_title"],
            content=article["article_content"],
            updateDate=curdate,
            articleIdx=article["article_idx"],
        )
        article_success = True if result.rowcount == 1 else False

        # rename file name for secure (한글지원X)
        # article['article_file'].filename = secure_filename(
        #     article['article_file'].filename)
        file_type = ""

        # new file doesn't existed only update article
        if article["article_file"].filename != "":

            # file path parsing
            file_type = os.path.splitext(article["article_file"].filename)[1]
            os_root = "C:" if platform.system() == "Windows" else "usr"

            if not os.path.exists(os_root + os.sep + UPLOAD_PATH):
                os.makedirs(os_root + os.sep + UPLOAD_PATH)

            new_file_path = os.path.join(
                os.sep,
                os_root + os.sep + UPLOAD_PATH + os.sep,
                article["article_file"].filename,
            )

            # original article already have file
            if article["file_updated"] == "true":

                article["article_file"].save(new_file_path)
                file_length = os.stat(new_file_path).st_size
                os.remove(article["prev_file_path"])
                file_result = conn.execute(
                    text(file_update_txt),
                    name=article["article_file"].filename,
                    type=file_type,
                    size=file_length,
                    articleIdx=article["article_idx"],
                    path=new_file_path,
                )
                file_success = True if file_result.rowcount == 1 else False
            else:

                article["article_file"].save(new_file_path)
                file_length = os.stat(new_file_path).st_size
                file_result = conn.execute(
                    text(file_insert_txt),
                    name=article["article_file"].filename,
                    type=file_type,
                    size=file_length,
                    articleIdx=article["article_idx"],
                    path=new_file_path,
                )
                file_success = True if file_result.rowcount == 1 else False

    return article["article_idx"], article_success and file_success


def check_password(request):
    data = request.get_json()
    password = data["password"]
    article_idx = data["articleIdx"]

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(" SELECT * FROM ARTICLE WHERE articleIdx = :article_idx")
        result = conn.execute(query, article_idx=article_idx)

    df_result = pd.DataFrame(result.fetchall(), columns=result.keys())
    article = df_result.to_dict("records")
    correct = True if (password == article[0]["password"]) else False
    return jsonify(correct=correct)


def reply_article(request):
    article_success = False
    file_success = True

    article = {
        "article_title": request.form["article_title"],
        # "article_title": html.escape(request.form['article_title']),
        "article_id": request.form["article_id"],
        "article_idx": request.form["article_idx"],
        "article_content": request.form["article_content"],
        "article_ref": request.form["article_ref"],
        "article_indent": request.form["article_indent"],
        "article_step": request.form["article_step"],
        "article_file": request.files["article_file"],
    }

    # 원글 ref의 답글 중 원글의 step보다 큰 것 + 1
    update_article_step(article)

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:

        query = text(
            "INSERT INTO ARTICLE(userId,title,content,ref,indent,step ) VALUES(:userId, :title, :content, :ref, :indent, :step)"
        )
        article_result = conn.execute(
            query,
            userId=article["article_id"],
            title=article["article_title"],
            content=article["article_content"],
            ref=article["article_ref"],
            indent=int(article["article_indent"]) + 1,
            step=int(article["article_step"]) + 1,
        )
        article_success = True if article_result.rowcount == 1 else False
        created_idx = conn.execute("SELECT LAST_INSERT_ID() AS id").fetchone()

        # save file

        # 한글 지원 X 주석처리
        # article['article_file'].filename = secure_filename(
        #     article['article_file'].filename)
        file_type = ""

        if article["article_file"].filename != "":
            file_type = os.path.splitext(article["article_file"].filename)[1]

            # 파일 확장자 불일치
            if file_type not in UPLOAD_EXTENSIONS:
                file_success = False
                delete_article_by_idx(created_idx["id"])
                return article_success and file_success

            os_root = "C:" if platform.system() == "Windows" else "usr"

            if not os.path.exists(os_root + os.sep + UPLOAD_PATH):
                os.makedirs(os_root + os.sep + UPLOAD_PATH)

            file_path = os.path.join(
                os.sep,
                os_root + os.sep + UPLOAD_PATH + os.sep,
                article["article_file"].filename,
            )
            article["article_file"].save(file_path)

            file_length = os.stat(file_path).st_size

            query = text(
                "INSERT INTO FILE(name,type,size, articleIdx, path) VALUES(:name, :type, :size, :articleIdx, :path)"
            )

            file_result = conn.execute(
                query,
                name=article["article_file"].filename,
                type=file_type,
                size=file_length,
                articleIdx=created_idx["id"],
                path=file_path,
            )

            file_success = True if file_result.rowcount == 1 else False

    return article_success and file_success


def update_article_step(origin_article):
    update_txt = """
                    UPDATE ARTICLE SET STEP=STEP+1 
                    WHERE REF=:ref AND STEP>:step
                 """

    engine = dbconn.mysql_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(update_txt),
            ref=origin_article["article_ref"],
            step=origin_article["article_step"],
        )
