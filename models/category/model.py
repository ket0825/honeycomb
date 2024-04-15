from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON
from sqlalchemy.orm import mapped_column
from database import Base

class Category(Base):
    __tablename__ = 'category'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    s_category = mapped_column(VARCHAR(30), nullable=False)
    m_category = mapped_column(VARCHAR(30), nullable=False)
    url = mapped_column(VARCHAR(1000), nullable=False)
    s_topics = mapped_column(JSON, nullable=True)
    m_topics = mapped_column(JSON, nullable=True)

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

