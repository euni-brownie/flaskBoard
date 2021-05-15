from sqlalchemy import create_engine


def mysql_engine(db_name='flaskboard'):
    '''
    sqlalchemy를 사용해 MySQL engine 작성
    '''
    host = 'localhost'
    port = 3306
    user = 'root'
    passwd = 'Ptbw@.c0m'

    engine = create_engine(
        f'mysql+pymysql://{user}:{passwd}@{host}:{port}/{db_name}')

    return engine
