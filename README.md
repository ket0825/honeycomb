# Honeycomb
### Web server + logic server
- Web server for cosmos-dashbaord UI and Chrome-extensions
- Logic server from Preview or Honeybee(Both are crawler) to MySQLDB
- Combine with honeycomb and MySQL DB by **docker compose**.
---------------

### Used Framework
- Flask, CORS
- SQLAlchemy
- Gunicorn
- Docker compose
- K8s (minikube)

----------------------------

### DB SCHEMA
https://ket0825.notion.site/DB-schema-Specification-a24e1a5bb2df4493bd2aed0c596eac68?pvs=4

### API SPECIFICATION
https://ket0825.notion.site/API-CALL-Specification-d04379dcd2fe487bac3ef1f6e51b870f?pvs=4

## Composition
- ### App
  - init db engine, session
------------------------------

- ### Models
  - **Category, IP, Product, ProductHistory, Review, Topic**
  - Defined Models by SQLAlchemy 2.0 convention

------------------------------

- ### Routes
  - #### Upsert logic
    - product match
    - update_detail_one
  - #### Upsert batch logic
    - upsert_review_batch
  
  - #### Select logic
  - path compression or query string
    - select_product_history
    - select_topic_by_type
    - etc

-------------------------------

- ### Docker compose
  - Connect MySQL DB and Honeycomb server

-------------------------------

- ### K8s
  - kubernetes manifest for Honeycomb server and MySQL DB server

-------------------------------

- ### Log
  - custom stdlib logger for Honeycomb server.

-----------------------------
- ### Assets
  - js and css from Cosmos-dashboard (TYPESCRIPT + VITE + REACT)

- ### Template
  - html from Cosmos-dashboard (TYPESCRIPT + VITE + REACT)

