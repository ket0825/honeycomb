from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_, bindparam, desc
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product_history.model import ProductHistory
from ..util.util import base10_to_base36, base36_to_base10, custom_response, print_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload
import re

product_history_route = Blueprint('product_history_route', __name__)
BATCH_SIZE = 20

# Use query string at caid and prid and timestamp.
@product_history_route.route('/api/product_history', methods=['GET'])
def select_product_history():
    try:        
        stmt = select(ProductHistory)                    
        if 'caid' in request.args.keys():
            caid = request.args.get('caid') 
            stmt = stmt.where(ProductHistory.caid==caid)    # for aggregation
        if 'prid' in request.args.keys():
            prid = request.args.get('prid')
            stmt = stmt.where(ProductHistory.prid==prid)    # for aggregation            
        if 'timestamp_count' in request.args.keys():
            timestamp_count = request.args.get('timestamp_count')
            stmt = stmt.order_by(desc(ProductHistory.timestamp)).limit(timestamp_count)    # for aggregation            
                        
        res = db_session.execute(stmt).scalars().all()        
        db_session.commit()

        return jsonify([row.to_dict() for row in res])
        
    except Exception as e:
        db_session.rollback()
        print_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()            
