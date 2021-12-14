FROM python:3.9

WORKDIR /media-backend

COPY src .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN export PATH="$PATH:/media-backend"

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "80"]

EXPOSE 80/tcp