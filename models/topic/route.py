from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam
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

topic_route = Blueprint('topic_route', __name__)
BATCH_SIZE = 20

# Use query string at topic_code and type and topic_sentiment.
# Use path parameter at reid.
@topic_route.route('/api/topic/<reid>', methods=['GET'])
def select_topic_by_reid(reid):
    try:
        stmt = select(Topic).where(Topic.reid==reid)                    
        if 'topic_code' in request.args.keys():
            topic_code = request.args.get('topic_code') 
            stmt = stmt.where(Topic.topic_code==topic_code)    # for aggregation
        if 'type' in request.args.keys():
            type = request.args.get('type')
            stmt = stmt.where(Topic.type==type)
        if 'sentiment_scale' in request.args.keys():
            sentiment_scale = request.args.get('sentiment_scale')
            stmt = stmt.where(Topic.sentiment_scale==sentiment_scale)
                        
        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        return jsonify([row.to_dict() for row in res])
        
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()            
