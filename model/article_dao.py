import connection as dbconn
import pandas as pd


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
