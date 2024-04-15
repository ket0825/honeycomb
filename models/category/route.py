from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine
from sqlalchemy import select, insert, update, delete, and_
from sqlalchemy import Table, func
from models.category.model import Category
from .util import base10_to_base36, base36_to_base10
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
        res = db_session.execute(stmt).scalars().all()
        # 모든 것이 필요하지 않다면...
        # jsonify([dict(id=post.id, name=post.name) for post in posts])
        
        if res:
            return jsonify([row.to_dict() for row in res])
        else:
            return Response(f"[ERROR] No data", status=404)
        
    except Exception as e:
        db_session.rollback()
        print(f"[ERROR] {e}")
        if current_app.debug:
            return Response(f"[ERROR] {e}", status=400)
        else:
            return Response(f"Fail!", status=400)
    finally:
        db_session.remove()

# 수작업이기에 batch insert가 아닌 one으로 처리함.
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
                            # Category.url.ilike(f"%{url}%"),
                        )    
                    )
            
            res = db_session.scalar(stmt)
            if res.url == url:
                print(f"Already exists category: {packet}")
                continue
            elif res.url != url:
                stmt = update(Category).where(
                    Category.m_category.ilike(f"%{m_category}%"),
                    Category.s_category.ilike(f"%{s_category}%"),
                ).values(url=url)
                db_session.execute(stmt)
                db_session.commit()
                data_changes = True
                if current_app.debug:
                    print(f"Updated category url: {packet}")
                else:
                    print(f"Updated category url")  
            else:
                status = "INSERTED"
                stmt = select(func.max(Category.id))
                q_result = db_session.scalar(stmt)            
                max_id = q_result+1 if q_result is not None else 0
                packet['caid'] = packet["type"] + base10_to_base36(max_id)
                stmt = insert(Category)
                db_session.execute(stmt, packet)
                db_session.commit()
                data_changes = True
                if current_app.debug:
                    print(f"Inserted category: {packet}")
                else:
                    print(f"Inserted category") 

        if data_changes:
            return Response(f"[SUCCESS] Insert Or Update", status=201)
        else:
            return Response(f"NO CHANGES", status=200)
        
    except Exception as e:
        db_session.rollback()
        print(f"[ERROR] {e}")
        return Response(f"Fail!", status=400)
    finally:
        db_session.remove()




@category_route.route('/api/category/s_topic', methods=['POST'])
def insert_s_topic():
    packets = request.get_json()
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
                            Category.url.ilike(f"%{url}%"),
                        )    
                    )
            
            res = db_session.scalar(stmt)
            if res:
                print(f"Already exists category: {packet}")
                continue
            
            stmt = select(func.max(Category.id))
            q_result = db_session.scalar(stmt)            
            max_id = q_result+1 if q_result is not None else 0
            packet['caid'] = packet["type"] + base10_to_base36(max_id)
            stmt = insert(Category)
            db_session.execute(stmt, packet)
            db_session.commit()
            return Response(f"[SUCCESS] Insert", status=201)
        
    except Exception as e:
        db_session.rollback()
        print(f"[ERROR] {e}")
        return Response(f"Fail!", status=400)
    finally:
        db_session.remove()
