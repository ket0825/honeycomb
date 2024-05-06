import sys
import os

from flask import Flask
from flask_cors import CORS
from database import db_session
from create_database import create_database
from database import init_db
from models.category.route import category_route
from models.product.route import product_route
from models.review.route import review_route
from models.ip.route import ip_route
from models.topic.route import topic_route
from models.product_history.route import product_history_route

from log import Logger

log = Logger.get_instance()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# request를 마친 후 session을 닫아버리게 만듦.
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


app.register_blueprint(category_route)
app.register_blueprint(product_route)
app.register_blueprint(review_route)
app.register_blueprint(ip_route)
app.register_blueprint(topic_route)
app.register_blueprint(product_history_route)
init_db()

@app.route('/health', methods=['GET'])
def health():
    return 'OK'
    

if __name__ == '__main__':
    port_num = sys.argv[1]
    app.run(port=port_num)
    # app.run(debug=True)
    # app.run(host='0.0.0.0') # 외부 접근 가능. public IP.
