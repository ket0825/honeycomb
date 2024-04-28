from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint
from sqlalchemy.orm import mapped_column
from database import Base

class Product(Base):
    __tablename__ = 'product'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # P.
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    prid = mapped_column(CHAR(10), nullable=True) # base36, P0..
    url = mapped_column(VARCHAR(1000), nullable=False)
    grade = mapped_column(FLOAT(precision=2, decimal_return_scale=1), nullable=False) 
    name = mapped_column(VARCHAR(100), nullable=False)
    lowest_price = mapped_column(Integer, nullable=False)
    review_count = mapped_column(Integer, nullable=False)
    match_nv_mid = mapped_column(VARCHAR(30), nullable=False)
    # Below mapped_columnscrawlers entered the product link (secondary-crawler).
    brand = mapped_column(VARCHAR(20), nullable=True)
    maker = mapped_column(VARCHAR(20), nullable=True)
    naver_spec = mapped_column(JSON, nullable=True) # with locations
    seller_spec = mapped_column(JSON, nullable=True) # with locations
    # if seller_spec: crawler get also image_urls.
    detail_image_urls = mapped_column(JSON, nullable=True)            
    
    __table_args__ = (
        UniqueConstraint('type','caid', 'id', 'match_nv_mid', name='uq_product_caid_prid'),
    )


    def to_dict(self):
        return {
            'id': self.id,
            'caid': self.caid,
            'prid': self.prid,
            'url': self.url,
            'grade': self.grade,
            'name': self.name,
            'lowest_price': self.lowest_price,
            'review_count': self.review_count,
            'brand': self.brand,
            'maker': self.maker,
            'naver_spec': self.naver_spec,
            'seller_spec': self.seller_spec,
            'detail_image_urls': self.detail_image_urls
        }