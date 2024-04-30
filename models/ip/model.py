from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint
from sqlalchemy.orm import mapped_column
from database import Base

class IP(Base):
    __tablename__ = 'ip'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    address = mapped_column(VARCHAR(30), nullable=False)
    country = mapped_column(VARCHAR(30), nullable=True)
    chrome_version = mapped_column(VARCHAR(200), nullable=True)
    naver = mapped_column(CHAR(10), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ip_address', name='uq_ip_address'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'country': self.country,
            'chrome_version': self.chrome_version,
            'naver': self.naver
        }