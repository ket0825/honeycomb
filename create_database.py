import pymysql
import traceback
from settings import DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DB_HOST

def create_database():
    try:
        conn = pymysql.connect(
                host=DB_HOST,            # 접속할 mysql server의 주소
                port=DB_PORT,        # 접속할 mysql server의 포트 번호
                user=DB_USER,     
                passwd=DB_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            sql = f'CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
            cursor.execute(sql)
            print('Database created!')

    except Exception as e:
        traceback.print_exc()
        pass

if __name__ == '__main__':
    create_database()