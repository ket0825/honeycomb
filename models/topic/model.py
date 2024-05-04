from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint, Index
from sqlalchemy.orm import mapped_column
from database import Base

class Topic(Base):
    __tablename__ = 'topic'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # T0
    tpid = mapped_column(CHAR(10), nullable=True) # base36, T0.. # 현재 없어도 됌.
    # prid = mapped_column(CHAR(10), nullable=False) # base36, P0.. join review table
    # caid = mapped_column(CHAR(10), nullable=False) # base36, C0.. join review table
    reid = mapped_column(CHAR(10), nullable=True) # base36, R0..
    text = mapped_column(VARCHAR(200), nullable=False)  # topic text (Could be deleted)
    topic_code = mapped_column(CHAR(50), nullable=False) # topic code (english)
    topic_name = mapped_column(VARCHAR(20), nullable=False) # topic name (korean)
    topic_score = mapped_column(Integer, nullable=False) # topic score
    start_position = mapped_column(Integer, nullable=False)
    end_position = mapped_column(Integer, nullable=False)
    positive_yn = mapped_column(CHAR(1), nullable=False) # topic sentiment (Y, N)
    sentiment_scale = mapped_column(Integer, nullable=False) # topic sentiment scale  

    __table_args__ = (
        UniqueConstraint('type', 'id', name='uq_topic_type_id'),
        # At production level. It should be indexed.
        Index('ix_reid', 'reid'), # reid (검색 key 목적)
        Index('ix_topic_code', 'topic_code', 'topic_score'), # topic_code (검색 key와 점수 목적)
        Index('ix_sentiment', 'positive_yn', 'sentiment_scale')  # sentiment (검색 key와 점수 목적)
    )

    

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'tpid': self.tpid,
            'reid': self.reid,
            'text': self.text,
            'topic_code': self.topic_code,
            'topic_name': self.topic_name,
            'topic_score': self.topic_score,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'topic_sentiment': self.positive_yn,
            'topic_sentiment_score': self.sentiment_scale
        }