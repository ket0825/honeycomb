from sqlalchemy import Integer, CHAR, VARCHAR, TIMESTAMP, FLOAT, JSON, UniqueConstraint, Index, func, desc, asc
from sqlalchemy.orm import mapped_column
from database import Base

class Product(Base):
    """
    ALTER TABLE cosmos.Product
    ADD COLUMN update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER detail_image_urls,
    ADD COLUMN topic_type VARCHAR(30) NULL AFTER prid;
    """
    __tablename__ = 'product'
    id = mapped_column(Integer, primary_key=True) # autoincrement.
    type = mapped_column(CHAR(3), nullable=False) # P.
    caid = mapped_column(CHAR(10), nullable=False) # base36, C0..
    prid = mapped_column(CHAR(10), nullable=True) # base36, P0..
    url = mapped_column(VARCHAR(500), nullable=False)
    grade = mapped_column(FLOAT(precision=2, decimal_return_scale=1), nullable=False) 
    name = mapped_column(VARCHAR(100), nullable=False)
    lowest_price = mapped_column(Integer, nullable=False)
    review_count = mapped_column(Integer, nullable=False)
    match_nv_mid = mapped_column(VARCHAR(30), nullable=False)
    # Below mapped_columns are updated when crawlers entered the product link (secondary-crawler).
    brand = mapped_column(VARCHAR(20), nullable=True)
    maker = mapped_column(VARCHAR(20), nullable=True)
    naver_spec = mapped_column(JSON, nullable=True) # with locations
    seller_spec = mapped_column(JSON, nullable=True) # with locations    
    # if seller_spec: crawler get also image_urls.
    detail_image_urls = mapped_column(JSON, nullable=True)            
    
    update_time = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    topic_type = mapped_column(VARCHAR(30), nullable=True) 
    
    __table_args__ = (
        UniqueConstraint('type', 'id', name='uq_product_type_id'),
        # Index('ix_caid', 'caid'), # caid (내부 검색 key)
        Index('ix_match_nv_mid', 'match_nv_mid'), # match_nv_mid (내부 검색 key)
        Index('ix_prid', 'prid'),  # prid (내부 검색 key)
        Index('ix_grade', 'grade'), # grade (정렬 목적)
        Index('ix_name', asc(name)), # name (검색 및 정렬 목적)
        Index('ix_lowest_price', "lowest_price"), # lowest_price (정렬 목적)
        Index('ix_review_count', 'review_count'), # review_count (정렬 목적)
        Index('ix_brand', 'brand'), # brand (검색 및 그룹화 목적)
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
            "match_nv_mid": self.match_nv_mid,
            'seller_spec': self.seller_spec,
            'detail_image_urls': self.detail_image_urls,
            'update_time': self.update_time,
            'topic_type': self.topic_type,            
        }