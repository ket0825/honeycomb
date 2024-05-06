import pymysql
import traceback
from settings import DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DB_HOST

try:
    conn = pymysql.connect(
            host=DB_HOST,            # 접속할 mysql server의 주소
            port=DB_PORT,        # 접속할 mysql server의 포트 번호
            user=DB_USER,     
            passwd=DB_PASSWORD,
            db=DB_NAME,         # 접속할 database명
            charset='utf8mb4',          # 'utf8' 등 문자 인코딩 설정 (한글 데이터가 깨지지 않도록)
            cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        sql = 'SELECT * FROM t'
        cursor.execute(sql)

except Exception as e:
    traceback.print_exc()
    pass
