from database import engine, db_session


def explain_query(query):
    query = query.compile(engine, compile_kwargs={"literal_binds": True})
    db_session.execute(f'EXPLAIN {query}')
    