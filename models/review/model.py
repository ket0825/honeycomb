from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint
from sqlalchemy.orm import mapped_column
from database import Base

class Review(Base):
    __tablename__ = 'review'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # R.
    prid = mapped_column(CHAR(10), nullable=False) # base36, P0..
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    reid = mapped_column(CHAR(10), nullable=True) # base36, R0..
    content = mapped_column(VARCHAR(2000), nullable=False)
    # our topics mapped_column.JSON, nullable=True)
    our_topics = mapped_column(JSON, nullable=True)
    quality_score = mapped_column(FLOAT(precision=5, decimal_return_scale=5), nullable=False)
    buy_option = mapped_column(VARCHAR(100), nullable=True)
    star_score = mapped_column(Integer, nullable=False)
    topic_count = mapped_column(Integer, nullable=False)
    topic_yn = mapped_column(CHAR(1), nullable=False)
    topics = mapped_column(JSON, nullable=True)
    user_id = mapped_column(CHAR(20), nullable=False, unique=True)
    aida_modify_time = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    mall_id = mapped_column(VARCHAR(30), nullable=False)
    mall_seq = mapped_column(VARCHAR(30), nullable=False)
    mall_name = mapped_column(VARCHAR(50), nullable=False)
    match_nv_mid = mapped_column(VARCHAR(30), nullable=False)
    nv_mid = mapped_column(VARCHAR(30), nullable=False)
    image_urls = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint('type', 'id', 'prid', name='uq_review_type_id_prid'),
    )