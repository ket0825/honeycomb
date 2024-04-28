from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from models.category.model import Category
from ..util.util import base10_to_base36, base36_to_base10, custom_response, print_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload
import re

product_route = Blueprint('product_route', __name__)
match_nv_mid_ptrn = re.compile(r'nvMid=(\d+)')

# Use query string at s_category and m_category.
# Use path parameter at caid.
@product_route.route('/api/product', defaults={"prid":None}, methods=['GET'])
@product_route.route('/api/product/<prid>', methods=['GET'])
def select_all(prid):
    try:
        stmt = select(Product)
        if prid:
            stmt = stmt.where(Product.prid.ilike(f"%{prid}%"))                    
        elif 'name' in request.args.keys():
            name = request.args.get('name') 
            stmt = stmt.where(Product.name.ilike(f"%{name}%"))
                        
        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        if res:
            return jsonify([row.to_dict() for row in res])
        else:
            return Response(f"[SUCCESS] No data", status=200)
        
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()            

"""
Upsert product overview at the first crawling
(Only id, caid, prid, url, grade, name, lowest_price, review_count)
"""
@product_route.route('/api/product/match', methods=['POST'])
def upsert_match():
    # bulk upsert 불가능. 이유는 autoincrement id => prid로 변환하는 과정이 필요하기 때문.
    try:
        packets = request.get_json()
        type = packets.get('type')
        assert type.startswith("P") and (0 <= int(type[1]) <= 9)
        
        caid_stmt = select(Category.caid).where(Category.s_category==packets.get('category'))
        caid = db_session.execute(caid_stmt).scalar_one()
        
        for packet in packets.get('items'):
            # packet validation
            if (not isinstance(packet, dict) 
                or not packet.get('grade') # empty string is False.
                or not packet.get('review_count') # empty string is False.
                or not isinstance(packet.get('review_count'), int)
                or not isinstance(packet.get('url'), str) 
                or not isinstance(packet.get('grade'), float)
                or not isinstance(packet.get('name'), str) 
                or not isinstance(packet.get('lowest_price'), int)
            ):
                print_debug_msg(current_app.debug, f"Invalid packet: {packet}", f"Invalid packet")
                continue            
            
            packet['caid'] = caid
            packet['match_nv_mid'] = match_nv_mid_ptrn.search(packet.get('url')).group(1)
            packet['type'] = type

            select_prid_stmt = select(Product.prid).where(Product.caid==caid, 
                                        or_(Product.match_nv_mid==packet['match_nv_mid'], 
                                            Product.name.ilike(f"%{packet['name']}%")))
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
                        
            

        # for packets in batch_generator(data, 10):            
        #     stmt = mysql_insert(Product).values(packets)
        #     upsert_stmt = stmt.on_duplicate_key_update(
        #         grade=stmt.inserted.grade,
        #         name=stmt.inserted.name,
        #         lowest_price=stmt.inserted.lowest_price,
        #         review_count=stmt.inserted.review_count
        #     )
            
        #     result = db_session.execute(upsert_stmt)

        #     inserted_ids = result.inserted_primary_key

        #     if inserted_ids[0]:
        #         print_debug_msg(current_app.debug, f"Inserted ids: {inserted_ids}", f"Inserted ids")
        #         prid_start = inserted_ids[0]
        #         prid_end = inserted_ids[-1] + 1

        #         for record_id, prid in zip(inserted_ids, range(prid_start, prid_end)):
        #             prid_value = base10_to_base36(prid)
        #             db_session.query(Product).filter_by(id=record_id).update({'prid': prid_value})
        #         # for id in inserted_ids:
        #         #     prid_value = base10_to_base36(id)
        #         #     update_stmt = update(Product).where(Product.id==id).values(prid=prid_value)
        #         #     db_session.execute(update_stmt)
            
        #     db_session.commit()
        
        return custom_response(current_app.debug, f"[SUCCESS] Success!", f"Success!", 200)

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()        
    
"""
Upsert product at detail page.
(Only brand, maker, naver_spec ,seller_spec, image_urls)
"""
@product_route.route('/api/product/detail', methods=['POST'])
def upsert_detail():
    try:
       pass
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()        
    

