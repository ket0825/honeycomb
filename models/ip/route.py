from flask import Blueprint, request, jsonify, Response, current_app
from database import db_session, metadata_obj, engine

from sqlalchemy import select, insert, update, delete, and_, or_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import Table, func
from models.ip.model import IP
from ..util.util import base10_to_base36, base36_to_base10, custom_response, log_debug_msg, batch_generator
from datetime import datetime
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import lazyload

ip_route = Blueprint('ip_route', __name__)


@ip_route.route('/api/ip', methods=['GET'])
def select_one():
    try:                
        if request.args.get('unused') == 'True':
            res = db_session.execute(select(IP).where(IP.naver == 'unused')).first()
            db_session.commit()            
        else:
            res = db_session.execute(select(IP)).scalars().all()
            db_session.commit()
            
        return jsonify([row.to_dict() for row in res])
                    
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()            


@ip_route.route('/api/ip', methods=['POST'])
def upsert_batch():
    # bulk upsert 불가능. 이유는 autoincrement id => prid로 변환하는 과정이 필요하기 때문.
    try:
        packets = request.get_json()        

        insert_list = []
        update_list = []
        address_list = []
        for packet in packets:
            # packet validation
            if (not isinstance(packet, dict) 
                or not isinstance(packet.get("address"), str)
                or not isinstance(packet.get('country'), str)                 
                or not isinstance(packet.get('user_agent'), str) 
                or not isinstance(packet.get('naver'), str)
            ):                
                log_debug_msg(current_app.debug, f"Invalid packet: {packet}", f"Invalid packet")
                continue            
            
            res = db_session.execute(select(IP).where(IP.address==packet.get('address'))).scalar_one_or_none()           
            
            # address 중복 체크
            if packet.get('address') in address_list:
                log_debug_msg(current_app.debug, f"Duplicate packet: {packet}", f"Duplicate packet")
                continue
            # address가 존재하면 update, 없으면 insert
            if res:                
                update_list.append(packet)
                address_list.append(packet.get('address'))
                continue
            else:
                insert_list.append(packet)
                address_list.append(packet.get('address'))
        
        if insert_list:
            for packet in insert_list:
                insert_stmt = insert(IP).values(packet)    
                db_session.execute(insert_stmt)
                db_session.commit()

        if update_list:
            for packet in update_list:
                update_stmt = update(IP).where(IP.address==packet.get('address')).values(
                    country=packet.get('country'),
                    user_agent=packet.get('user_agent'),
                    naver=packet.get('naver'),
                    timestamp=datetime.now(),
                )
                db_session.execute(update_stmt)
                db_session.commit()
        
        return custom_response(current_app.debug, f"[SUCCESS] Insert packet length: {len(insert_list)}, Update packet length: {len(update_list)}", f"[SUCCESS] Insert and update", 200)

    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail! {e}", 400)
    finally:
        db_session.remove()        


@ip_route.route('/api/ip/<address>', methods=['DELETE'])
def delete_one(address):
    try:
        delete_stmt = delete(IP).where(IP.address==address)
        result = db_session.execute(delete_stmt)
        db_session.commit()

        if result.rowcount == 0:
            return custom_response(current_app.debug, f"[ERROR] ip_address: {address} not found", f"[ERROR] Not found", 404)
        else:
            return custom_response(current_app.debug, f"[SUCCESS] Deleted ip_address: {address}", f"[SUCCESS] Deleted", 200)
    except Exception as e:
        db_session.rollback()
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!: {e}", 400)
    finally:
        db_session.remove()


