FROM python:3.10.0

LABEL version="0.1.0"

ARG stage=dev




WORKDIR /app

COPY . .

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt





# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
CMD ["sh", "-c", "python create_database.py && python create_tables.py && gunicorn --workers 4 --bind 0.0.0.0:5000 -m 007 wsgi:app"]

