import os
import json

reviews_dir = r"./data/reviews"

extra_battery_allow_label = ["커스터마이징", "그립감", "색감", "로고없음", "재질","디자인",
     "인증", "발열", "과충전방지", "과전류","안전",
     "AS", "환불", "문의", "교환", "수리", "보험", "배송","서비스", "배송/포장/발송",
     "멀티포트", "거치", "부착", "디스플레이", "잔량표시", "충전표시","기능",
     "고속충전", "동시충전","저전력", "무선충전", "맥세이프", "배터리충전속도","충전",
     "사이즈", "무게","휴대성",
    "기내반입", "수명", "친환경", "구성품", "케이블", "파우치", "케이스","기타",
    "호환성","배터리를충전하는호환성",
    "배터리용량"]

def data_cleansing(reviews_dir):
    for reviews_fp in os.listdir(reviews_dir):
        if not reviews_fp.endswith(".json"):
            print(f"Skipping {reviews_fp}")
            continue

        with open(f"{reviews_dir}/{reviews_fp}", 'r', encoding='utf-8-sig') as f:
            data = json.load(f)    

        for review in data:
            our_topics = review.get("our_topics")
        
            if not our_topics:
                continue

            cleansed_topics = []
            for topic in our_topics:
                if (not topic.get('text')
                    or not topic.get("topic")
                    or not topic.get("start_pos")
                    or not topic.get("end_pos")
                    or not topic.get("positive_yn")
                    or not topic.get("sentiment_scale")
                    or not topic.get("topic_score")
                    ):
                    continue
            
                topic_name = topic.get("topic")
                
                if topic_name not in extra_battery_allow_label:
                    print("CHECK THIS TOPIC NAME:", topic_name)
                    print("filepath:",reviews_fp)
                    continue

                cleansed_topics.append(topic)
            
            review["our_topics"] = cleansed_topics

if __name__ == "__main__":
    data_cleansing(reviews_dir)
    