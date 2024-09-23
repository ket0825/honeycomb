from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session
from sqlalchemy import select, insert, update, delete, and_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.category.model import Category
from ..util.util import base10_to_base36, base36_to_base10, custom_response, log_debug_msg
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload

category_route = Blueprint('category_route', __name__)
"""
Test: 
[
    {
        "type": "C0",
        "s_category": "keyboard",
        "m_category": "computer",
        "url": "https://search.shopping.naver.com/search/category/100005369?adQuery&catId=50001204&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list",
        "s_topics": [],
        "m_topics": []
    },
    {
        "type": "C0",
        "s_category": "extra_battery",
        "m_category": "mobile",
        "url": "https://search.shopping.naver.com/search/category/100005088?adQuery&catId=50001380&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list",
        "s_topics": [],
        "m_topics": []
    },
    {
        "type": "CA",
        "s_category": "",
        "m_category": "",
        "url": "",
        "s_topics": [],
        "m_topics": []
    }
]
"""

# Use query string at s_category and m_category.
# Use path parameter at caid.
@category_route.route('/api/category', defaults={'caid': None}, methods=['GET'])
@category_route.route('/api/category/<caid>', methods=['GET'])
def select_all(caid):
    try:        
        stmt = select(Category)
        if caid:
            stmt = stmt.where(Category.caid.ilike(f"{caid}%"))
        if 's_category' in request.args:
            category = request.args.get('s_category') 
            stmt = stmt.where(Category.s_category.ilike(f"{category}%"))
        if 'm_category' in request.args:
            category = request.args.get('m_category') 
            stmt = stmt.where(Category.m_category.ilike(f"{category}%"))
        
        res = db_session.execute(stmt).scalars().all()
                
        log_debug_msg(current_app.debug, f"[SUCCESS] {len(res)}", f"[SUCCESS] {len(res)}")
        db_session.commit()
        
        if res:
            return jsonify([row.to_dict() for row in res])
        else:
            return Response(f"[SUCCESS] No data", status=404)
        
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail! {e}")
        return custom_response(current_app.debug, f"[ERROR] Fail {e}", f"Fail! {e}", 400)        
    finally:
        db_session.remove()


@category_route.route('/api/category', methods=['POST'])
# Upsert s_topic (Should be same url with db and packet)
# {s_topic: {data: [], timestamp: current_timestamp}}
def upsert_one():
    packets = request.get_json()
    data_change = False
    try:
        for packet in packets:
            assert isinstance(packet, dict)            
            assert isinstance(packet.get('s_topics'), list)
            s_topics = {
                "data": packet.get('s_topics'),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }           
            packet['s_topics'] = s_topics
            
            type = packet.get('type')
            assert type.startswith("C") and (0 <= int(type[1]) <= 9)

            m_category = packet.get('m_category')
            s_category = packet.get('s_category')

            caid_stmt = select(Category.caid).where(
                and_(
                    Category.m_category.ilike(f"{m_category}%"),
                    Category.s_category.ilike(f"{s_category}"), # s_category must be same with packet.
                    Category.type.ilike(f"{type}"), # Type must be same with packet.
                )
            )
            caid = db_session.scalar(caid_stmt)        

            if caid:                
                update_stmt = update(Category).where(Category.caid==caid).values(packet)
                db_session.execute(update_stmt)

                data_change = True
            else:
                insert_stmt = insert(Category).values(packet)
                result = db_session.execute(insert_stmt)                       
                inserted_id = result.inserted_primary_key
                if inserted_id[0]:
                    caid = packet['type'] + base10_to_base36(inserted_id[0])
                    update_stmt = update(Category).where(Category.id==inserted_id[0]).values(caid=caid)
                    db_session.execute(update_stmt)              
                else:
                    log_debug_msg(current_app.debug, f"[FAIL] insert: {packet}", f"[FAIL] insert: {packet}")

            db_session.commit()
        
        if data_change:
            log_debug_msg(current_app.debug, f"[SUCCESS] Update and insert: {len(packets)}", f"[SUCCESS] Update and insert: {len(packets)}")
            return custom_response(current_app.debug, f"[SUCCESS] Update and insert: {len(packets)}", f"[SUCCESS] Update and insert: {len(packets)}", 201)                                           
        else:
            log_debug_msg(current_app.debug, f"[SUCCESS] Update and insert: {len(packets)}", f"[SUCCESS] Update and insert: {len(packets)}")
            return custom_response(current_app.debug, f"[SUCCESS] Insert: {len(packets)}", f"[SUCCESS] Insert: {len(packets)}", 201)                                           

    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[SUCCESS] Update and insert: {len(packets)}", f"[SUCCESS] Update and insert: {len(packets)}")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!: {e}", 400)        
    finally:
        db_session.remove()
