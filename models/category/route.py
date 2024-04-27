from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine
from sqlalchemy import select, insert, update, delete, and_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.category.model import Category
from ..util.util import base10_to_base36, base36_to_base10, custom_response, print_debug_msg
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
@category_route.route('/api/category', methods=['GET'])
def select_all():
    try:
        stmt = select(Category)
        if 's_category' in request.args.keys():
            category = request.args.get('s_category') 
            stmt = stmt.where(Category.s_category.ilike(f"%{category}%"))
        elif 'm_category' in request.args.keys():
            category = request.args.get('m_category') 
            stmt = stmt.where(Category.m_category.ilike(f"%{category}%"))
        elif 'caid' in request.args.keys():
            caid = request.args.get('caid') 
            stmt = stmt.where(Category.caid.ilike(f"%{caid}%"))
        
        res = db_session.execute(stmt).scalars().all()
        # 모든 것이 필요하지 않다면...
        # jsonify([dict(id=post.id, name=post.name) for post in posts])
        
        if res:
            return jsonify([row.to_dict() for row in res])
        else:
            return Response(f"[ERROR] No data", status=404)
        
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)        
    finally:
        db_session.remove()

# 수작업이기에 batch insert가 아닌 one으로 처리함.
# url 부분만 upsert 담당. TODO: s_topics, m_topics도 upsert 해야함(아래 insert_s_topic과 통합 예정).
@category_route.route('/api/category/one', methods=['POST'])
def insert_one():
    packets = request.get_json()
    data_changes = False
    try:
        for packet in packets:
            assert isinstance(packet, dict)

            type = packet.get('type')
            assert type.startswith("C") and (0 <= int(type[1]) <= 9)

            m_category = packet.get('m_category')
            s_category = packet.get('s_category')
            url = packet.get('url')

            stmt = select(Category).where(
                        and_(
                            Category.m_category.ilike(f"%{m_category}%"),
                            Category.s_category.ilike(f"%{s_category}%"),
                        )    
                    )
            # Already exists
            res = db_session.scalar(stmt)
            if res.url == url:
                print_debug_msg(current_app.debug, f"Already exists category: {packet}", f"Already exists category")
                continue
            
            # Update url and s_topics and m_topics
            elif (res.url != url 
                  or res.s_topics != packet.get('s_topics') 
                  or res.m_topics != packet.get('m_topics')
                ):
                stmt = update(Category).where(
                    Category.m_category.ilike(f"%{m_category}%"),
                    Category.s_category.ilike(f"%{s_category}%"),
                ).values(url=url)
                db_session.execute(stmt)
                db_session.commit()
                data_changes = True
                print_debug_msg(current_app.debug, f"Updated category: {packet}", f"Updated category")
                
            # Insert
            else:
                stmt = select(func.max(Category.id))
                q_result = db_session.scalar(stmt)            
                max_id = q_result+1 if q_result is not None else 0
                packet['caid'] = packet["type"] + base10_to_base36(max_id)
                stmt = insert(Category)
                db_session.execute(stmt, packet)
                db_session.commit()
                data_changes = True
                print_debug_msg(current_app.debug, f"Inserted category: {packet}", f"Inserted category")                

        if data_changes:
            return Response(f"[SUCCESS] Insert Or Update", status=201)
        else:
            return Response(f"NO CHANGES", status=200)
        
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)
    finally:
        db_session.remove()


@category_route.route('/api/category/s-topic', methods=['POST'])
# Upsert s_topic (Should be same url with db and packet)
# {s_topic: {data: [], timestamp: current_timestamp}}
# TODO: integrate with insert_one
def upsert_s_topic():
    packets = request.get_json()
    data_change = False
    try:
        for packet in packets:
            assert isinstance(packet, dict)            
            assert isinstance(packet.get('s_topics'), list)
            type = packet.get('type')
            assert type.startswith("C") and (0 <= int(type[1]) <= 9)

            m_category = packet.get('m_category')
            s_category = packet.get('s_category')
            url = packet.get('url')

            select_stmt = select(Category).where(
                        and_(
                            Category.m_category.ilike(f"%{m_category}%"),
                            Category.s_category.ilike(f"%{s_category}%"),
                            Category.url.ilike(f"%{url}%"),
                        )    
                    )            
            res = db_session.scalar(select_stmt)

            if not res:
                print_debug_msg(current_app.debug, f"No Content: {packet}", f"No Content", status=204)              
                continue

            # s_topics upsert    
            s_topics = {
                "data": packet.get('s_topics'),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }               
            insert_stmt = mysql_insert(Category).values(
                            id = res.id,
                            caid = res.caid,
                            s_category = res.s_category,
                            m_category = res.m_category,
                            url = res.url,
                            s_topics=s_topics,
                            )                                   
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                s_topics=insert_stmt.inserted.s_topics,
            )            
            db_session.execute(on_duplicate_key_stmt)
            db_session.commit()
            data_change = True
            print_debug_msg(current_app.debug, f"UPSERT SUCCESS: {packet}", f"UPSERT SUCCESS")            
        
        if data_change:
            return custom_response(current_app.debug, f"UPSERT SUCCESS", f"UPSERT SUCCESS", 201)                                           
        else:
            return custom_response(current_app.debug, f"No Content", f"No Content", 204)                                                              

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 400)        
    finally:
        db_session.remove()
