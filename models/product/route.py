from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine
from sqlalchemy import select, insert, update, delete, and_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.product.model import Product
from ..util.util import base10_to_base36, base36_to_base10, custom_response, print_debug_msg
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload

product_route = Blueprint('product_route', __name__)

@product_route.route('/product', methods=['GET'])
def select_all():
    try:
        stmt = select(Product)
        if 's_product' in request.args.keys():
            product = request.args.get('s_product') 
            stmt = stmt.where(Product.s_product.ilike(f"%{product}%"))
        elif 'm_product' in request.args.keys():
            product = request.args.get('m_product') 
            stmt = stmt.where(Product.m_product.ilike(f"%{product}%"))
        elif 'paid' in request.args.keys():
            paid = request.args.get('paid') 
            stmt = stmt.where(Product.paid.ilike(f"%{paid}%"))
        
        res = db_session.execute(stmt).scalars().all()
        # 모든 것이 필요하지 않다면...
        # jsonify([dict(id=post.id, name=post.name) for post in posts])
        
        if res:
            return jsonify([post.to_dict() for post in res])
        else:
            return custom_response(404, 'Not Found')
    except Exception as e:
        print_debug_msg(e)
        return custom_response(500, 'Internal Server Error')