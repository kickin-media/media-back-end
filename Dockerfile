FROM python:3.11-slim

LABEL org.opencontainers.image.source=https://github.com/kickin-media/media-back-end

ENV ENVIRONMENT=development
ENV DB_CONNECTION="mysql+pymysql://kickin:kickin@localhost/media_backend"

WORKDIR /media-backend

COPY src .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN export PATH="$PATH:/media-backend"

CMD ["./start.sh"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
  CMD curl -f http://localhost:80/status

EXPOSE 80/tcp
