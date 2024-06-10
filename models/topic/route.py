from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from models.review.model import Review
from models.topic.model import Topic
from models.category.model import Category
from ..util.util import base10_to_base36, base36_to_base10, custom_response, log_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload
import re
import time

topic_route = Blueprint('topic_route', __name__)
BATCH_SIZE = 20

# Use query string at topic_code and type and topic_sentiment...
# Type should be provided with the prefix of "OT" or "RT" at query string.
# Query modified by Cardinality of the columns.
@topic_route.route('/api/topic', methods=['GET'])
def select_topic_by_type():
    try:
        if 'type' in request.args.keys() and 'caid' in request.args.keys():
            type = request.args.get('type')
            caid = request.args.get('caid')            
            stmt = select(Topic).join(Review, Review.reid==Topic.reid).where(
                and_(
                Review.caid==caid,
                Topic.type==type
                ))          
            # explained_query = text(str(stmt.compile(compile_kwargs={"literal_binds": True})))
            # print(db_session.execute(text(f"EXPLAIN {explained_query}")).fetchall())  
            # t1 = time.time()                            
            res = db_session.execute(stmt).scalars().all()        
            db_session.commit()
            # t2 = time.time()
            # log_debug_msg(current_app.debug, f"[INFO] spend time: {t2-t1}", f"Success!")
            # t1 = time.time()                            
            # [row.to_dict() for row in res]
            # t2 = time.time()
            # log_debug_msg(current_app.debug, f"[INFO] spend time at to_dict: {t2-t1}", f"Success!")
            return jsonify([row.to_dict() for row in res])
        
        if 'type' in request.args.keys() and "prid" in request.args.keys():
            type = request.args.get('type')
            if type.startswith("OT"):
                prid = request.args.get('prid')
                stmt = select(Topic).where(Topic.prid==prid)
            elif type.startswith("RT"):
                prid = request.args.get("prid")            
                stmt = select(Topic).join(Review, Review.reid==Topic.reid).where(
                and_(
                Review.prid==prid,
                Topic.type==type
                ))          
            # explained_query = text(str(stmt.compile(compile_kwargs={"literal_binds": True})))
            # print(db_session.execute(text(f"EXPLAIN {explained_query}")).fetchall())  
            # t1 = time.time()                            
            res = db_session.execute(stmt).scalars().all()        
            # db_session.commit()
            # t2 = time.time()
            # log_debug_msg(current_app.debug, f"[INFO] spend time: {t2-t1}", f"Success!")
            return jsonify([row.to_dict() for row in res])            
                
        if "reid" in request.args.keys():
            reid = request.args.get('reid')
            stmt = stmt.where(Topic.reid==reid)
        if 'topic_code' in request.args.keys():
            topic_code = request.args.get('topic_code') 
            stmt = stmt.where(Topic.topic_code==topic_code)    # for aggregation. Only one column exists at Both OT and RT.
        if 'topic_score' in request.args.keys():
            topic_score = request.args.get('topic_score') 
            stmt = stmt.where(Topic.topic_code==topic_score)        
        if 'positive_yn' in request.args.keys():
            positive_yn = request.args.get('positive_yn')
            stmt = stmt.where(Topic.positive_yn==positive_yn)
        if 'sentiment_scale' in request.args.keys():
            sentiment_scale = request.args.get('sentiment_scale')
            stmt = stmt.where(Topic.sentiment_scale==sentiment_scale)
        if 'type' in request.args.keys():
            type = request.args.get('type')            
            stmt = select(Topic).where(Topic.type==type)            

        # explained_query = text(str(stmt.compile(compile_kwargs={"literal_binds": True})))
        # print(db_session.execute(text(f"EXPLAIN {explained_query}")).fetchall())
        # res = db_session.execute(stmt).scalars().all()        
        # db_session.commit()        
        # log_debug_msg(current_app.debug, f"[INFO] {t2-t1}", f"Success!")
        return jsonify([row.to_dict() for row in res])
        
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()                  
