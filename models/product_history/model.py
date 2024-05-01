from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint
from sqlalchemy.orm import mapped_column
from database import Base

class ProductHistory(Base):
    __tablename__ = 'product_history'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    prid = mapped_column(CHAR(10), nullable=False) # base36, P0..
    review_count = mapped_column(Integer, nullable=False)
    grade = mapped_column(FLOAT(precision=2, decimal_return_scale=1), nullable=False)
    lowest_price = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(TIMESTAMP, nullable=False)

    __table_args__ = (
        UniqueConstraint('prid','timestamp', name='uq_prod_hist_prid_timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'caid': self.caid,
            'prid': self.prid,
            'review_count': self.review_count,
            'grade': self.grade,
            'lowest_price': self.lowest_price,
            'timestamp': self.timestamp
        }