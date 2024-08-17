import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from settings import DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DB_HOST
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# gunicorn은 프로세스 단위로 동작하기 때문에, 프로세스 단위로 engine을 만들어서 사용함.
# worker 설정 3.
# 프로세스 단위로 하나의 engine을 만들어서 사용.
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
                    query_cache_size=1200, pool_size=5, max_overflow=10, echo=False, pool_recycle=3600, pool_timeout=30)

# connection pool 관련.
"""https://spoqa.github.io/2018/01/17/connection-pool-of-sqlalchemy.html"""
# Base 애들 create_all로 engine을 이용하여 전부 생성.
# 결국 서비스마다 그만의 퍼포먼스와 장비 한계치가 있으니만큼 내부에서 스트레스 테스트를 통한 벤치마킹으로 적정 값을 뽑아내는 것을 추천합니다.
# Session이 실제로 요청을 보내는 시점에 연결을 시도함! : Note that the Engine and its underlying Pool do not establish the first actual DBAPI connection until the Engine.connect() or Engine.begin() methods are called. Either of these methods may also be invoked by other SQLAlchemy Engine dependent objects such as the ORM Session object when they first require database connectivity. In this way, Engine and Pool can be said to have a lazy initialization behavior.


# scoped_session을 이용하여 thread마다 session을 생성.
db_session = scoped_session(
    sessionmaker(
        autocommit=False,                                         
        autoflush=False,
        expire_on_commit=False,
        bind=engine
        )
    )
# 기본 세션 관리는 serialiable로 관리.
# https://docs.sqlalchemy.org/en/14/orm/session_transaction.html
# 웹서비스에는 repeatable_read로 관리.

metadata_obj = MetaData()

Base = declarative_base()

def init_db():
    Base.metadata.create_all(engine)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR) # sqlalchemy 로그 레벨을 ERROR로 설정.
