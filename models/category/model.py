from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint
from sqlalchemy.orm import mapped_column
from database import Base

class Category(Base):
    __tablename__ = 'category'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # C.
    caid = mapped_column(CHAR(10), nullable=True) # base36, C0..
    s_category = mapped_column(VARCHAR(30), nullable=False)
    m_category = mapped_column(VARCHAR(30), nullable=False)
    url = mapped_column(VARCHAR(500), nullable=False)
    s_topics = mapped_column(JSON, nullable=True)
    m_topics = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint('type', 'id', 's_category', name='uq_type_id_s_category'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'caid': self.caid,
            's_category': self.s_category,
            'm_category': self.m_category,
            'url': self.url,
            's_topics': self.s_topics,
            'm_topics': self.m_topics
        }

