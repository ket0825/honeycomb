from database import engine, db_session
from sqlalchemy import text

# http://chongmoa.com/sql/8840 참고


def explain_query(query):
    query = query.compile(engine, compile_kwargs={"literal_binds": True})
    explain_stmt = text(f"EXPLAIN {query}")
    res = db_session.execute(explain_stmt).fetchall()
    for row in res:
        print(row)
    