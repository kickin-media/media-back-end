FROM python:3.9

ENV ENVIRONMENT=development
ENV DB_CONNECTION="mysql+pymysql://kickin:kickin@localhost/media_backend"

WORKDIR /media-backend

COPY src .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN export PATH="$PATH:/media-backend"

CMD ["./start.sh"]

EXPOSE 80/tcp