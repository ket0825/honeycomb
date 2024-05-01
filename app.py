from flask import Flask, request
from database import db_session
from database import init_db
from models.category.route import category_route
from models.product.route import product_route
from models.review.route import review_route
from models.ip.route import ip_route
app = Flask(__name__)
# 현재 Review TABLE이 만들어져있지 않음.

# request를 마친 후 session을 닫아버리게 만듦.
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

app.register_blueprint(category_route)
app.register_blueprint(product_route)
app.register_blueprint(review_route)
app.register_blueprint(ip_route)

if __name__ == '__main__':
    init_db()
    app.run(port=5000)
    # app.run(debug=True)

    # app.run(host='0.0.0.0') # 외부 접근 가능. public IP.


# 변수 규칙
# URL의 변수 부분을 추가하기위해 여러분은 <variable_name>``으로 URL에 특별한 영역으로 표시해야된다. 그 부분은 함수의 키워드 인수로써 넘어간다.  선택적으로, ``<converter:variable_name> 으로 규칙을 표시하여 변환기를 추가할 수 있다. 여기 멋진 예제가 있다.

# @app.route('/user/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return 'User %s' % username

# @app.route('/post/<int:post_id>')
# def show_post(post_id):
#     # show the post with the given id, the id is an integer
#     return 'Post %d' % post_id
# 다음과 같은 변환기를 제공한다. :

# int	accepts integers
# float	like int but for floating point values
# path	like the default but also accepts slashes
"""
https://flask-docs-kr.readthedocs.io/ko/latest/quickstart.html
"""