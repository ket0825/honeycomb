from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam
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
BATCH_SIZE = 20

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
"""
@review_route.route('/api/review', methods=['POST'])
#TODO: 각 packet마다 prid, caid, type 추가해야 함. 예시 packets 만들어야 함.
#TODO: Needs packets logic.
def upsert_review_batch():    
    try:
        packets = request.get_json()
        type = packets.get('type')
        assert type.startswith("R") and (0 <= int(type[1]) <= 9)
        
        # if prid is not given, then use match_nv_mid to find prid.
        prid = packets.get('prid')
        if not prid:
            match_nv_mid = packets.get('match_nv_mid')
            prid_stmt = select(Product.prid).where(Product.match_nv_mid==match_nv_mid)
            prid = db_session.execute(prid_stmt).scalar_one()

        caid_stmt = select(Category.caid).where(Category.s_category==packets.get('category'))
        caid = db_session.execute(caid_stmt).scalar_one()        

        reviews = []

        # packet validation and reformatting
        for review in packets.get('reviews'):                        
            # packet validation
            if (not isinstance(review, dict) 
                or not isinstance(review.get('id'), str) 
                or not isinstance(review.get('aidaModifyTime'), str)
                or not isinstance(review.get('matchNvMid'), str)
                or not isinstance(review.get('nvMid'), str)
                or not isinstance(review.get('qualityScore'), (float, int))
                or not isinstance(review.get('starScore'), int) 
            ):
                print_debug_msg(current_app.debug, f"Invalid packet: {review}", f"Invalid packet")
                continue            
            # packet reformatting. Later, it will be used for insert.
            # TODO: crawler should provide these fields.
            packet = {
                'type': type,
                'prid': prid,
                'caid': caid,
                'content': review.get('content'),
                'our_topics' : review.get('our_topics') if review.get('our_topics') else [],
                'n_review_id' : review.get('id'),
                'quality_score' : review.get('qualityScore'),
                'buy_option' : review.get('buyOption'),
                'star_score' : review.get('starScore'),
                'topic_count' : review.get('topicCount'),
                'topic_yn' : review.get('topicYn'),
                'topics' : review.get('topics'),
                'user_id' : review.get('userId'),
                'aida_modify_time':review.get('aidaModifyTime'),
                'mall_id':review.get('mallId'),
                'mall_seq':review.get('mallSeq'),
                'mall_name':review.get('mallName'),
                'match_nv_mid':match_nv_mid,
                'nv_mid':review.get('nvMid'),
                'image_urls':review.get('imageUrls') if review.get('imageUrls') else [],
            }

            reviews.append(packet)
        
        # check exists.        
        select_stmt = select(Review.n_review_id).where(Review.n_review_id.in_([review.get('n_review_id') for review in reviews]))
        exists = db_session.execute(select_stmt).scalars().all()

        for review_batch in batch_generator(reviews, BATCH_SIZE): # batch size
            # insert or update
            insert_batch = [review for review in review_batch if review.get('n_review_id') not in exists]

            # TODO: update_batch should check data same or not.
            update_batch = [review for review in review_batch if review.get('n_review_id') in exists]

            if insert_batch:
                insert_stmt = insert(Review).values(insert_batch)
                db_session.execute(insert_stmt)    

                inserted_id_type = db_session.execute(
                    select(Review.id, Review.type).where(
                        Review.n_review_id.in_([row.get('n_review_id') for row in insert_batch])
                        )
                    ).all()


                update_reid = [
                    {
                    "id_val": id,
                    "type": type,
                    "reid": type+base10_to_base36(id)
                    } 
                    for id, type in inserted_id_type]

                update_stmt = update(Review).where(
                    Review.id == bindparam('id_val')).values(reid=bindparam('reid'))    # not id, id_val should be used.
                db_session.connection().execute(update_stmt, update_reid) # For batch update, use connection.
                db_session.commit()            
                print_debug_msg(current_app.debug, f"[SUCCESS] Insert {insert_batch} batch", f"[SUCCESS] Insert {len(insert_batch)} batch")
            
            if update_batch:
                update_stmt = update(Review).where(
                    Review.n_review_id == bindparam('n_review_id_val')).values(
                        aida_modify_time=bindparam('aida_modify_time'),
                        content=bindparam('content'),
                        our_topics=bindparam('our_topics'),
                        quality_score=bindparam('quality_score'),
                        star_score=bindparam('star_score'),
                        topic_count=bindparam('topic_count'),
                        topic_yn=bindparam('topic_yn'),
                        topics=bindparam('topics'),
                        nv_mid=bindparam('nv_mid'),
                        image_urls=bindparam('image_urls')                    
                    )
                
                for row in update_batch: # for batch update, need to reformat.
                    row['n_review_id_val'] = row.pop('n_review_id')                
                
                db_session.connection().execute(update_stmt, update_batch) # for batch update, use connection.
                db_session.commit()
                print_debug_msg(current_app.debug, f"[SUCCESS] Update {update_batch} batch", f"[SUCCESS] Update {len(update_batch)} batch")
            
        return custom_response(current_app.debug, f"[SUCCESS] Insert and Update batch: {len(reviews)}", f"[SUCCESS] Insert and Update batch: {len(reviews)}", 200)
        

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()        