from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint, text
from sqlalchemy.orm import mapped_column
from database import Base

class IP(Base):
    __tablename__ = 'ip'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    address = mapped_column(VARCHAR(30), nullable=False)
    country = mapped_column(VARCHAR(30), nullable=True)
    user_agent = mapped_column(VARCHAR(200), nullable=True)
    naver = mapped_column(CHAR(10), nullable=False)
    timestamp = mapped_column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        UniqueConstraint('address', name='uq_ip_address'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'country': self.country,
            'user_agent': self.user_agent,
            'naver': self.naver,
            'timestamp': self.timestamp,
        }