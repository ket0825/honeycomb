from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from models.review.model import Review
from models.category.model import Category
from ..util.util import base10_to_base36, base36_to_base10, custom_response, print_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload
import re

review_route = Blueprint('review_route', __name__)

# Use query string at s_category and m_category.
# Use path parameter at caid.
@review_route.route('/api/review', defaults={"reid":None}, methods=['GET'])
@review_route.route('/api/review/<reid>', methods=['GET'])
def select_all(reid):
    try:
        stmt = select(Review)
        if reid:
            stmt = stmt.where(Review.reid==reid)                    
        elif 'prid' in request.args.keys():
            prid = request.args.get('prid') 
            stmt = stmt.where(Review.prid==prid)    # for aggregation
                        
        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        return jsonify([row.to_dict() for row in res])
        
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()            

"""
Upsert product overview at the first crawling
(Only id, caid, prid, url, grade, name, lowest_price, review_count)
"""
@review_route.route('/api/product', methods=['POST'])
#TODO: 각 packet마다 prid, caid, type 추가해야 함. 예시 packets 만들어야 함.
def upsert_review():
    # bulk upsert 불가능. 이유는 autoincrement id => prid로 변환하는 과정이 필요하기 때문.
    try:
        packets = request.get_json()
        type = packets.get('type')
        assert type.startswith("R") and (0 <= int(type[1]) <= 9)
        
        caid_stmt = select(Category.caid).where(Category.s_category==packets.get('category'))
        caid = db_session.execute(caid_stmt).scalar_one()
        
        for packet in packets.get('items'):
            # packet validation
            if (not isinstance(packet, dict) 
                or not isinstance(packet.get('review_count'), int)
                or not isinstance(packet.get('url'), str) 
                or not isinstance(packet.get('grade'), (float, int))
                or not isinstance(packet.get('name'), str) 
                or not isinstance(packet.get('lowest_price'), int)
                or not isinstance(packet.get('match_nv_mid'), str)
            ):
                print_debug_msg(current_app.debug, f"Invalid packet: {packet}", f"Invalid packet")
                continue            
            
            packet['caid'] = caid

            packet['type'] = type

            select_prid_stmt = select(Product.prid).where(Product.caid==caid, 
                                        or_(Product.match_nv_mid==packet['match_nv_mid'], 
                                            Product.name.ilike(f"{packet['name']}")))
            prid_exist = db_session.execute(select_prid_stmt).scalar_one_or_none()

            if prid_exist:
                update_stmt = update(Product).where(
                    and_(Product.prid==prid_exist, Product.caid==caid)
                    ).values(
                        name=packet['name'], 
                        lowest_price=packet['lowest_price'], 
                        review_count=packet['review_count'],
                        match_nv_mid=packet['match_nv_mid'],
                        grade=packet['grade']
                        )
                db_session.execute(update_stmt)
                db_session.commit()
            else:                          
                insert_stmt = insert(Product).values(packet)
                result = db_session.execute(insert_stmt)
                inserted_ids = result.inserted_primary_key
                if inserted_ids[0]:
                    prid = packet.get('type') + base10_to_base36(inserted_ids[0])
                    update_prid = update(Product).where(Product.id==inserted_ids[0]).values(prid=prid)
                    db_session.execute(update_prid)
                    db_session.commit()
                else:
                    db_session.rollback()
                    print_debug_msg(current_app.debug, f"Fail to insert: {packet}", f"Fail to insert")                                               
        
        return custom_response(current_app.debug, f"[SUCCESS] Success!", f"Success!", 200)

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()        
    

@review_route.route('/api/product/detail/one', methods=['POST'])
def update_detail_one():
    """
    [SINGLE PACKET] Update product at detail page.

    For brand, maker, naver_spec ,seller_spec, image_urls.

    But, if product could be changed at the time, then update all fields.

    ex) {} [SINGLE PACKET]
    """
    try:
        packet = request.get_json()
        
        prid = packet.get('prid')
        caid = packet.get('caid')
        prid_validate = prid[0] == 'P' and (0 <= int(prid[1]) <= 9)
        caid_validate = caid[0] == 'C' and (0 <= int(caid[1]) <= 9)
        if not prid_validate or not caid_validate:
            return custom_response(current_app.debug, f"[ERROR] Invalid packet: {packet}", f"Fail!", 400)

        update_stmt = update(Product).where(
            and_(Product.prid==prid, Product.caid==caid)
        ).values( 
            grade = packet.get('grade'),            
            name = packet.get('name'),
            lowest_price = packet.get('lowest_price'),
            review_count = packet.get('review_count'),
            url = packet.get('url'),
            brand=packet.get('brand'),
            maker=packet.get('maker'),
            naver_spec=packet.get('naver_spec'),
            seller_spec=packet.get('seller_spec'),
            detail_image_urls=packet.get('detail_image_urls')            
        )
        db_session.execute(update_stmt)

        # Insert history
        select_prod_hist = select(ProductHistory).where(ProductHistory.prid==prid).order_by(ProductHistory.timestamp.desc()).limit(1)
        last_hist = db_session.execute(select_prod_hist).scalar_one_or_none()
        
        if (not last_hist  # if there is no history
            or last_hist.grade != packet.get('grade')  # if there is any changes
            or last_hist.lowest_price != packet.get('lowest_price') 
            or last_hist.review_count != packet.get('review_count')
            ):
            insert_stmt = insert(ProductHistory).values(
                caid=caid,
                prid=prid,
                review_count=packet.get('review_count'),
                grade=packet.get('grade'),
                lowest_price=packet.get('lowest_price'),
                timestamp=datetime.now()
            )
            db_session.execute(insert_stmt)
        else:
            db_session.commit()
            return custom_response(current_app.debug, f"[SUCCESS] No changes: {packet}", f"[SUCCESS] No changes", 201)
        
        db_session.commit()       
        return custom_response(current_app.debug, f"[SUCCESS] Success!", f"Success!", 200)
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()        
    

