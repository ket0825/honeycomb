# Honeycomb
### 웹서버와 로직 서버가 같이 있습니다
- Preview 크롬 익스텐션 서비스와 cosmos-dashbaord UI를 위한 웹서버입니다
- Preview 크롤러에서 데이터를 로직서버에서 받아와 MySQL DB에 적재합니다
- **docker compose**로 Honeycomb과 MySQL을 결합하였습니다
  
---------------

### 사용된 기술
- Flask, CORS
- SQLAlchemy
- Gunicorn
- Docker compose
- K8s (minikube test)

----------------------------

### DB 스키마
https://ket0825.notion.site/DB-schema-Specification-a24e1a5bb2df4493bd2aed0c596eac68?pvs=4

### API 명세
https://ket0825.notion.site/API-CALL-Specification-d04379dcd2fe487bac3ef1f6e51b870f?pvs=4

## 구성요소
- ### App
  - DB 엔진과 스레드 단위 세션을 init 합니다
------------------------------

- ### Models
  - **Category, IP, Product, ProductHistory, Review, Topic** 테이블이 있습니다
  - SQLAlchemy 2.0 컨벤션에 따라 정의되어 있습니다

------------------------------

- ### Routes
  - #### Upsert 로직
    - product match
    - update_detail_one
  - #### Upsert 배치
    - upsert_review_batch
  
  - #### Select 로직
  - 경로 파라미터나 쿼리 스트링으로 데이터를 받습니다
    - select_product_history
    - select_topic_by_type
    - etc

-------------------------------

- ### Docker compose
  - MySQL DB와 honeycomb 서버를 연결합니다

-------------------------------

- ### K8s  
  - 쿠버네티스 명세가 있습니다

-------------------------------

- ### Log
  - 커스텀 로거가 있습니다

-----------------------------
- ### Assets
  - cosmos dashboard를 위한 js와 css 파일이 있습니다 (cosmos dashboard: https://github.com/ket0825/cosmos-dashboard)

- ### Template
  - cosmos dashboard를 위한 html 파일이 있습니다
