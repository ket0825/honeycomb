import traceback

from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from models.review.model import Review
from models.category.model import Category
from models.topic.model import Topic
from ..util.util import base10_to_base36, base36_to_base10, custom_response, log_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload
from settings import topic_name_to_code

from common_utils.track_resources import track_usage_context
from common_utils.explain_query import explain_query

from datetime import datetime


review_route = Blueprint('review_route', __name__)
BATCH_SIZE = 20

# Use query string at s_category and m_category.
# Use path parameter at caid.

@review_route.route('/api/review/<caid>', methods=['GET'])
def select_all(caid):
    try:        
        stmt = select(Review).where(Review.caid==caid)
            
        if 'prid' in request.args.keys():
            prid = request.args.get('prid') 
            stmt = stmt.where(Review.prid==prid)    # for aggregation
        if 'reid' in request.args.keys():
            reid = request.args.get('reid')
            stmt = stmt.where(Review.reid==reid)                        

        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        return jsonify([row.to_dict() for row in res])
        
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"[ERROR] {e}")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!: {e}", 500)
    finally:
        db_session.remove()            

# check if need update review
@review_route.route('/api/review/need_update', methods=['POST'])
def check_if_need_update():
    """
    request_body: {
        ...,
        "n_review_id": "aida_modify_time"            
        }
    """
    try:        
        packet = request.get_json()
        assert isinstance(packet, dict)                

        select_id_time_stmt = select(Review.n_review_id, Review.aida_modify_time).where(
                Review.n_review_id.in_(
                    packet.keys()
                )      
            )                              
        id_time = db_session.execute(select_id_time_stmt).all()                
        exists = {row[0]: row[1] for row in id_time} # n_review_id: aida_modify_time                        
               
        accept_review_ids = [   
            n_review_id for n_review_id in packet.keys() if not exists.get(n_review_id) or exists.get(n_review_id) < datetime.strptime(packet.get(n_review_id), "%Y-%m-%d %H:%M:%S")
        ]
        
        db_session.commit()
        return jsonify(accept_review_ids)
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"[ERROR] {e}!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"[ERROR] {e}!", 500)
    finally:
        db_session.remove()

"""
1. Upsert product overview at the first crawling.
2. Delete all topics with reid in reid_set and insert all our_topics.
"""
#TODO: 각 packet마다 prid, caid, type 추가해야 함. 예시 packets 만들어야 함.
#TODO: Needs packets logic.
@review_route.route('/api/review', methods=['POST'])
def upsert_review_batch():    
    try:
        packets = request.get_json()        
        type = packets.get('type')
        assert type.startswith("R") and (0 <= int(type[1]) <= 9)
        
        # if prid is not given, then use match_nv_mid to find prid.
        match_nv_mid = packets.get('match_nv_mid')
        prid = packets.get('prid')
        s_category = packets.get('category')

        # explain query 검증 완료.        
        if not prid and not s_category:
            prid_caid_stmt = select(Product.prid, Product.caid).where(Product.match_nv_mid==match_nv_mid)            
            res = db_session.execute(prid_caid_stmt).all()
            prid, caid = res[0]
        elif prid: # prid is given.
            caid_stmt = select(Product.caid).where(Product.prid==prid)     
            caid = db_session.execute(caid_stmt).scalar()
        elif s_category: # s_category and match_nv_mid are given.
            prid_stmt = select(Product.prid).where(Product.match_nv_mid==match_nv_mid)            
            prid = db_session.execute(prid_stmt).scalar()
            caid_stmt = select(Category.caid).where(Category.s_category==s_category)            
            caid = db_session.execute(caid_stmt).scalar()
        else:
            raise Exception(f"Invalid input: {prid}, {s_category}, {match_nv_mid}")
            
        reviews = []

        # 체크 완료.
        # packet validation and reformatting
        for review in packets.get('reviews'):                        
            # packet validation
            if (
                not isinstance(review, dict) 
                or not isinstance(review.get('id'), str) 
                or not isinstance(review.get('aidaModifyTime'), str)
                or not isinstance(review.get('matchNvMid'), str)
                or not isinstance(review.get('nvMid'), str)
                or not isinstance(review.get('qualityScore'), (float, int))
                or not isinstance(review.get('starScore'), int) 
            ):
                log_debug_msg(current_app.debug, f"Invalid packet: {review}", f"Invalid packet: {review}")
                continue            
            # packet reformatting. Later, it will be used for insert.
            # TODO: crawler should provide these fields.
            packet = {
                'type': type,
                'prid': prid,
                'caid': caid,
                'content': review.get('content'),
                'our_topics' : review.get('our_topics') if review.get('our_topics') else [],
                'our_topics_yn' : "Y" if review.get('our_topics') else "N",
                'n_review_id' : review.get('id'),
                'quality_score' : review.get('qualityScore'),
                'buy_option' : review.get('buyOption'),
                'star_score' : review.get('starScore'),
                'user_id' : review.get('userId'),
                
                'topic_count': review.get('topicCount'),
                'topic_yn': review.get('topicYn'),
                'topics': review.get('topics'),
                    
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
        # 여기서 index 안 걸려있는거 찾음!              
        select_stmt = select(Review.n_review_id, Review.reid) \
            .where(
                Review.n_review_id.in_(
                    [review.get('n_review_id') for review in reviews]
                )
            )          
              
        exists = db_session.execute(select_stmt).all()
        exists = {row[0]: row[1] for row in exists} # n_review_id: reid

        for review_batch in batch_generator(reviews, batch_size=BATCH_SIZE): # batch size
            # insert or update 
            insert_batch = [review for review in review_batch if review.get('n_review_id') not in exists]

            # TODO: update_batch should check data same or not. 
            # 아니면 크롤링 단에서 체크완료.
            update_batch = [review for review in review_batch if review.get('n_review_id') in exists]
            
            # reid tagging at update batch
            for row in update_batch:    # update 
                row['reid'] = exists.get(row.get('n_review_id'))
            
            our_topics = []
            reid_set = set()

            if insert_batch:
                # insert batch without our_topics               
                insert_stmt = insert(Review).values(
                    type=bindparam('type'),
                    prid=bindparam('prid'),
                    caid=bindparam('caid'),
                    content=bindparam('content'),
                    our_topics_yn=bindparam('our_topics_yn'),
                    n_review_id=bindparam('n_review_id'),
                    quality_score=bindparam('quality_score'),
                    buy_option=bindparam('buy_option'),
                    star_score=bindparam('star_score'),
                    
                    topic_count=bindparam('topic_count'),
                    topic_yn=bindparam('topic_yn'),
                    topics=bindparam('topics'),
                    
                    user_id=bindparam('user_id'),
                    aida_modify_time=bindparam('aida_modify_time'),
                    mall_id=bindparam('mall_id'),
                    mall_seq=bindparam('mall_seq'),
                    mall_name=bindparam('mall_name'),
                    match_nv_mid=bindparam('match_nv_mid'),
                    nv_mid=bindparam('nv_mid'),
                    image_urls=bindparam('image_urls'),
                )
                db_session.execute(insert_stmt, insert_batch)    

                inserted_id_type = db_session.execute(
                    select(Review.id, Review.type).where(
                        Review.n_review_id.in_([row.get('n_review_id') for row in insert_batch])
                        )
                    ).all()

                update_reid = [{
                    "id_val": id,
                    "type": type,
                    "reid": type+base10_to_base36(id)
                    } for id, type in inserted_id_type]

                update_stmt = update(Review).where(
                    Review.id == bindparam('id_val')).values(reid=bindparam('reid')
                                                             )    # not id, id_val should be used.
                db_session.connection().execute(update_stmt, update_reid) # For batch update, use connection.

                # topic table reid tagging.            
                for review, reid_obj in zip(insert_batch, update_reid):
                    if review.get('our_topics_yn') == 'N':
                        continue
                            
                    reid = reid_obj.get('reid')                                                                
                    reid_set.add(reid)
                    for our_topic in review.get('our_topics'):                        
                        if (our_topic.get('text') == "" 
                            or our_topic.get('topic') == ""
                            or our_topic.get('end_pos') == 0
                            or our_topic.get('positive_yn') == ""     
                            or not our_topic.get('topic_score') 
                            ):
                            continue
                        our_topic['reid'] = reid
                        our_topic['prid'] = prid
                        our_topics.append(our_topic)                                             

                            
                log_debug_msg(current_app.debug, f"[SUCCESS] Insert {insert_batch} batch", f"[SUCCESS] Insert {len(insert_batch)} batch")
            
            if update_batch:
                update_stmt = update(Review).where(
                    Review.n_review_id == bindparam('n_review_id_val')).values(
                        aida_modify_time=bindparam('aida_modify_time'),
                        content=bindparam('content'),
                        # our_topics=bindparam('our_topics'),
                        our_topics_yn=bindparam('our_topics_yn'),
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
                    for our_topic in row['our_topics']:
                        if (our_topic.get('text') == "" 
                            or our_topic.get('topic') == ""
                            or our_topic.get('end_pos') == 0
                            or our_topic.get('positive_yn') == ""                            
                            or not our_topic.get('topic_score') 
                            ):
                            continue
                        our_topic['reid'] = row['reid']                        
                        our_topics.append(our_topic)
                        reid_set.add(row['reid'])
                
                db_session.connection().execute(update_stmt, update_batch) # for batch update, use connection.
                
                log_debug_msg(current_app.debug, f"[SUCCESS] Update {update_batch} batch", f"[SUCCESS] Update {len(update_batch)} batch")

            if our_topics:
                # for performance, batch insert and don't Update 
                # 1. delete all topics with reid in reid_set                
                # Batch delete is more efficient than batch insert.
                delete_stmt = delete(Topic).where(Topic.reid.in_(reid_set))
                db_session.execute(delete_stmt)
                

                for our_topic in our_topics:                    
                    topic_name = our_topic.get('topic')                    
                    del our_topic['topic'] # topic name is not needed in topic table.
                    
                    our_topic['type'] = 'RT0' # Review Topic
                    our_topic['topic_name'] = topic_name                    
                    our_topic['topic_code'] = topic_name_to_code.get(topic_name) # topic name convert to topic code.
                    our_topic['prid'] = prid
                    if our_topic['topic_code'] == None:
                        log_debug_msg(current_app.debug, f"[ERROR] Invalid topic name: {topic_name}", f"[ERROR] Invalid topic name: {topic_name}")                            

                # 2. insert all our_topics
                # topic sample: 
                # {"type":"RT0", 'text': '품질이 뛰어나요', 'topic_code': 'quality', 'topic_name': '품질', 'topic_score': 1, 'start_pos': 0, 'end_pos': 7, 'positive_yn': 'Y', 'sentiment_scale': 2}
                for topic_batch in batch_generator(our_topics, 20): # For preventing overhead.
                    insert_stmt = insert(Topic).values(topic_batch)
                    db_session.execute(insert_stmt)    
                    log_debug_msg(current_app.debug, f"[SUCCESS] Insert topic {topic_batch[0]} to {topic_batch[-1]} batch", f"[SUCCESS] Insert topic {len(our_topics)} batch")
                    
            # commit by batch          
            db_session.commit()
            
        log_debug_msg(current_app.debug, f"[SUCCESS] Insert and Update batch: {len(reviews)}", f"[SUCCESS]")    
        return custom_response(current_app.debug, f"[SUCCESS] Insert and Update batch: {len(reviews)}", f"[SUCCESS] Insert and Update batch: {len(reviews)}", 200)
        
    except Exception as e:
        db_session.rollback()
        tb = traceback.format_exc()
        log_debug_msg(current_app.debug, f"[ERROR] {tb}", f"[ERROR] {tb}")
        return custom_response(current_app.debug, f"[ERROR] {tb}", f"[ERROR] {e}", 400)
    finally:
        db_session.remove()        
