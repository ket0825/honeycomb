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

import pandas as pd
import numpy as np

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
        
        if 'type' in request.args.keys() and 'prid' in request.args.keys() and 'topic_code' in request.args.keys():
            type = request.args.get('type')
            if type.startswith("OT"):
                prid = request.args.get('prid')
                stmt = select(Topic).where(
                and_(
                Topic.prid==prid,
                Topic.type==type,
                Topic.topic_code==request.args.get('topic_code')
                ))        
            elif type.startswith("RT"):
                prid = request.args.get("prid")            
                stmt = select(Topic).join(Review, Review.reid==Topic.reid).where(
                and_(
                Review.prid==prid,
                Topic.type==type,
                Topic.topic_code==request.args.get('topic_code')
                ))                                       
            res = db_session.execute(stmt).scalars().all()        
            db_session.commit()            
            return jsonify([row.to_dict() for row in res])
        
        if 'type' in request.args.keys() and "prid" in request.args.keys():
            type = request.args.get('type')
            if type.startswith("OT"):
                prid = request.args.get('prid')
                stmt = select(Topic).where(
                and_(
                Topic.prid==prid,
                Topic.type==type
                ))        
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
        
        res = db_session.execute(stmt).scalars().all()        

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


@topic_route.route('/api/topic/kano_model', methods=['GET'])
def get_kano_model_data():
    try:
        if 'type' in request.args.keys() and 'caid' in request.args.keys():
            type = request.args.get('type')
            caid = request.args.get('caid')            
            stmt = select(Topic).join(Review, Review.reid==Topic.reid).where(
                and_(
                Review.caid==caid,
                Topic.type==type
                ))          
                                 
            res = db_session.execute(stmt).scalars().all()        
            db_session.commit()

            df = pd.DataFrame([row.to_dict() for row in res])
            # 카테고리 내 토픽 빈도 계산
            category_topic_df = df.groupby(['topic_code']).agg({'topic_code':'count'}).rename(columns={'topic_code':'whole_topic_count'}).reset_index()
            category_topic_counts = category_topic_df['whole_topic_count'].sum()

            # 제품 내 토픽 빈도 계산
            product_topic_df = df.groupby(['prid', 'topic_code']).agg({'id':'count'}).rename(columns={'id':'topic_code_count'}).reset_index()

            # 제품 내 전체 토픽 빈도 계산
            topics_per_product_df = product_topic_df.groupby(['prid']).agg({'topic_code_count':'sum'}).rename(columns={'topic_code_count':'product_per_whole_topic_code'}).reset_index()

            # 데이터 병합
            merged_df = pd.merge(product_topic_df, topics_per_product_df, on='prid')
            merged_df['category_topic_counts'] = category_topic_counts
            merged_df = pd.merge(merged_df, category_topic_df, on='topic_code')

            # TF 계산: 제품 내 토픽 빈도 / 제품 내 전체 토픽 빈도
            merged_df['topic_frequency'] = merged_df['topic_code_count'] / merged_df['product_per_whole_topic_code']


            # ITF 계산: log(전체 토픽 수 / (총 토픽 출현 수)) 약간 다름. 나오는 것 모두가 중요한 것으로 봄. 나오는 항목만 따지기에 +1을 하지 않음.
            merged_df['inverse_topic_frequency'] = np.log(category_topic_counts / (merged_df['whole_topic_count']))

            # # TF-ITF 계산
            merged_df['tf_itf'] = merged_df['topic_frequency'] * merged_df['inverse_topic_frequency']

            # # KANO 모델과 연계를 위한 전처리
            kano_df = merged_df[['prid', 'topic_code', 'tf_itf']]

            # 평균으로 하는 이유: 위에서 topic_frequency 계산에 비율이 반영되어 있기 때문에 단순히 평균을 내는 것이 맞다고 판단함.
            whole_topic_kano_df = kano_df.groupby(['topic_code']).agg({'tf_itf':'mean'}).rename(columns={'tf_itf':'whole_topic_tf_itf'}).reset_index()

            # TF-ITF에 L2 정규화 적용
            whole_topic_kano_df['l2_norm_tf_itf'] = whole_topic_kano_df['whole_topic_tf_itf'] / np.sqrt(np.square(whole_topic_kano_df['whole_topic_tf_itf']).sum())

            whole_topic_kano_df = pd.merge(whole_topic_kano_df, category_topic_df, on='topic_code')

            sentiment_df = df[['topic_code', 'positive_yn', 'sentiment_scale']]

            sentiment_df['positive_coef'] = sentiment_df['positive_yn'].apply(lambda x: 1 if x == 'Y' else -1)
            sentiment_df['sentiment_score'] = sentiment_df['positive_coef']* sentiment_df['sentiment_scale']

            sentiment_df = sentiment_df.groupby(['topic_code']).agg({'sentiment_score':'mean'}).reset_index()
            sentiment_df['z_sentiment_score'] = (sentiment_df['sentiment_score'] - sentiment_df['sentiment_score'].mean()) / sentiment_df['sentiment_score'].std()
            sentiment_df.drop(['sentiment_score'], axis=1, inplace=True)

            kano_model_df = pd.merge(whole_topic_kano_df, sentiment_df, on='topic_code')
            
            # kano_dict = [{'id':record['topic_code'], 
            #               "data":[{'x': record['l2_norm_tf_itf'], 'y': record['z_sentiment_score'], "size": record['whole_topic_count']}]} 
            #               for record in kano_model_df.to_dict('records')]

            
            
            

            return jsonify([{'id':record['topic_code'], 
                          "data":[{'x': record['l2_norm_tf_itf'], 'y': record['z_sentiment_score'], "size": record['whole_topic_count']}]} 
                          for record in kano_model_df.to_dict('records')])
  
        else:
            return custom_response(current_app.debug, f"[ERROR] No type and caid", f"Fail!", 500)
        
    except Exception as e:
        db_session.rollback()
        log_debug_msg(current_app.debug, f"[ERROR] {e}", f"Fail!")
        return custom_response(current_app.debug, f"[ERROR] {e}", f"Fail!", 500)
    finally:
        db_session.remove()   

