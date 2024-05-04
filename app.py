from flask import Flask
from flask_cors import CORS
from database import db_session
from database import init_db
from models.category.route import category_route
from models.product.route import product_route
from models.review.route import review_route
from models.ip.route import ip_route
from models.topic.route import topic_route
from models.product_history.route import product_history_route
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

if __name__ == '__main__':
    init_db()
    app.run(port=5000)
    # app.run(debug=True)
    # app.run(host='0.0.0.0') # 외부 접근 가능. public IP.
