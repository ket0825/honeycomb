from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint, Index
from sqlalchemy.orm import mapped_column
from database import Base

class Review(Base):
    __tablename__ = 'review'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # R.
    prid = mapped_column(CHAR(10), nullable=False) # base36, P0..
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    reid = mapped_column(CHAR(10), nullable=True) # base36, R0..
    content = mapped_column(VARCHAR(10000), nullable=False)
    # our_topics = mapped_column(JSON, nullable=True),
    our_topics_yn = mapped_column(CHAR(1), nullable=False)
    n_review_id = mapped_column(VARCHAR(100), nullable=False)
    quality_score = mapped_column(FLOAT(precision=5, decimal_return_scale=5), nullable=False)
    buy_option = mapped_column(VARCHAR(100), nullable=True)
    star_score = mapped_column(Integer, nullable=False)
    topic_count = mapped_column(Integer, nullable=False)
    topic_yn = mapped_column(CHAR(1), nullable=False)
    topics = mapped_column(JSON, nullable=True)
    user_id = mapped_column(CHAR(20), nullable=False)
    aida_modify_time = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    mall_id = mapped_column(VARCHAR(30), nullable=False)
    mall_seq = mapped_column(VARCHAR(30), nullable=False)
    mall_name = mapped_column(VARCHAR(50), nullable=True)
    match_nv_mid = mapped_column(VARCHAR(30), nullable=False)    
    nv_mid = mapped_column(VARCHAR(30), nullable=False)
    image_urls = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint('type', 'id', name='uq_review_type_id'),
        Index('ix_prid', 'prid'),  # prid (aggregate 목적)
        # Index('ix_caid', 'caid'), # caid (aggregate 목적)
        Index('ix_reid', 'reid'), # reid (검색 key 목적)
        Index('n_v_review_id', 'n_review_id'), # n_review_id 조회 확인 목적.
        Index('ix_our_topics_yn', 'our_topics_yn'), # our_topics_yn (aggregate 목적)        
    )

    def to_dict(self):
        return {
            'id': self.id, 
            'type': self.type,
            'prid': self.prid,
            'caid': self.caid,
            'reid': self.reid, # R0..
            'content': self.content,
            'our_topics': self.our_topics,
            'n_review_id': self.n_review_id,
            'quality_score': self.quality_score,
            'buy_option': self.buy_option,
            'star_score': self.star_score,
            'topic_count': self.topic_count,
            'topic_yn': self.topic_yn,
            'topics': self.topics,
            'user_id': self.user_id,
            'aida_modify_time': self.aida_modify_time,
            'mall_id': self.mall_id,
            'mall_seq': self.mall_seq,
            'mall_name': self.mall_name,
            'match_nv_mid': self.match_nv_mid,
            'nv_mid': self.nv_mid,
            'image_urls': self.image_urls
        }