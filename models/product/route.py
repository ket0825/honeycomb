from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from models.product_history.model import ProductHistory
from models.category.model import Category
from models.topic.model import Topic
from ..util.util import base10_to_base36, base36_to_base10, custom_response, log_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload

from settings import topic_name_to_code
import re
import traceback

product_route = Blueprint('product_route', __name__)

# Use query string at s_category and m_category.
# Use path parameter at caid.
@product_route.route('/api/product', defaults={"prid":None}, methods=['GET'])
@product_route.route('/api/product/<prid>', methods=['GET'])
def select_all(prid):
    try:
        stmt = select(Product)
        if prid:
            stmt = stmt.where(Product.prid==prid)                    
        if 'match_nv_mid' in request.args.keys():
            match_nv_mid = request.args.get('match_nv_mid')
            stmt = stmt.where(Product.match_nv_mid==match_nv_mid)
                    
        # join vs query twice
        if 's_category' in request.args.keys():
            s_category = request.args.get('s_category')
            stmt = stmt.join(Category, Category.caid==Product.caid).where(Category.s_category==s_category)
        elif 'caid' in request.args.keys():
            caid = request.args.get('caid')
            stmt = stmt.where(Product.caid==caid)
                        
        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        if res:
            return jsonify([row.to_dict() for row in res])
        else:
            return Response(f"[SUCCESS] No data", status=200)
        
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"[ERROR] {e}", 500)
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
                or not isinstance(packet.get('review_count'), int)
                or not isinstance(packet.get('url'), str) 
                or not isinstance(packet.get('grade'), (float, int))
                or not isinstance(packet.get('name'), str) 
                or not isinstance(packet.get('lowest_price'), int)
                or not isinstance(packet.get('match_nv_mid'), str)
            ):
                log_debug_msg(current_app.debug, f"Invalid packet: {packet}", f"Invalid packet: {packet}")
                continue            
            
            packet['caid'] = caid

            packet['type'] = type

            # if match_nv_mid or name is already exist and caid is same, then update.
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
                log_debug_msg(current_app.debug, f"Update: {packet}", f"Update: {packet}")
            else:                          
                insert_stmt = insert(Product).values(packet)
                result = db_session.execute(insert_stmt)
                inserted_ids = result.inserted_primary_key
                if inserted_ids[0]:
                    prid = packet.get('type') + base10_to_base36(inserted_ids[0])
                    update_prid = update(Product).where(Product.id==inserted_ids[0]).values(prid=prid)
                    db_session.execute(update_prid)
                    db_session.commit()
                    log_debug_msg(current_app.debug, f"Insert: {packet}", f"Insert: {packet}")
                else:
                    db_session.rollback()
                    log_debug_msg(current_app.debug, f"Fail to insert: {packet}", f"Fail to insert: {packet}")                                               
        
        return custom_response(current_app.debug, f"[SUCCESS] Success!", f"Success!", 200)

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!: {e}", 400)
    finally:
        db_session.remove()        
    

@product_route.route('/api/product/detail/one', methods=['POST'])
def update_detail_one():
    #TODO: insert to Topic about OCR.
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
            return custom_response(current_app.debug, f"[ERROR] Invalid packet: {packet}", f"Fail!: {e}", 400)

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

        # Insert topic. (Real time predict 기준. Topic을 바로 삭제함.)
        if packet.get('seller_spec'):
            seller_spec = packet.get('seller_spec')
            our_topics = []                    
            
            for img_spec in seller_spec:                
                if img_spec["img_str"] != "": # not empty string.
                # first element in img_spec is our topics.
                    if img_spec.get("our_topics"):
                        our_topics.append(img_spec["our_topics"])

            if our_topics:
                for idx, image_topics in enumerate(our_topics):                    
                    for topic in image_topics:
                        topic['prid'] = prid
                        topic_name = topic.get('topic')            
                        topic['topic_name'] = topic_name
                        topic['type'] = "OT0"
                        topic['image_number'] = idx
                        del topic['topic']
                        print(topic)

                        topic['topic_code'] = topic_name_to_code.get(topic_name)
                        if topic['topic_code'] is None: # 알려만 주고 넘어감.
                            log_debug_msg(current_app.debug, f"[ERROR] Invalid topic: {topic_name}, text: {topic['text']}", f"Invalid topic: {topic_name}, text: {topic['text']}")
                            continue
                    
                delete_stmt = delete(Topic).where(Topic.prid == prid, Topic.type == "OT0")
                db_session.execute(delete_stmt)
                
                insert_stmt = insert(Topic).values(
                        type=bindparam('type'),
                        prid=bindparam('prid'),
                        text=bindparam('text'),
                        topic_name=bindparam('topic_name'),
                        topic_code=bindparam('topic_code'),
                        start_pos=bindparam('start_pos'),
                        end_pos=bindparam('end_pos'),
                        image_number=bindparam('image_number'),
                        bbox=bindparam('bbox'),                    
                    )
                db_session.execute(insert_stmt, our_topics)
            
        # Insert history
        select_prod_hist = select(ProductHistory).where(ProductHistory.prid==prid).order_by(ProductHistory.timestamp.desc()).limit(1)
        last_hist = db_session.execute(select_prod_hist).scalar_one_or_none()
        
        data_updated = False
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
            data_updated = True
            db_session.execute(insert_stmt)
                
        db_session.commit()
        log_debug_msg(current_app.debug, f"Update: {packet}", f"Update prid: {prid}")        
        
        if data_updated:
            log_debug_msg(current_app.debug, f"Data Updated: {data_updated}", f"Data_updated: {data_updated}")
            return custom_response(current_app.debug, f"[SUCCESS] History updated: {data_updated}", f"[SUCCESS] History updated: {data_updated}", 201)
        else:
            return custom_response(current_app.debug, f"[SUCCESS] Update packet: {packet}", f"[SUCCESS] Update packet", 201)
    except Exception as e:
        db_session.rollback()
        trace = traceback.format_exc()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"[ERROR] {trace}")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"[ERROR] {trace}", 400)
    finally:
        db_session.remove()        
    

