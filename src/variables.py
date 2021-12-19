import os

VALID_APP_ENVIRONMENTS = ['development', 'staging', 'production']

DB_CONNECTION_STRING = os.getenv('DB_CONNECTION', 'mysql+pymysql://kickin:kickin@localhost/media_backend')

CORS_ORIGINS = {
    'production': [],
    'staging': [],
    'development': ['http://localhost:3000'],
}
