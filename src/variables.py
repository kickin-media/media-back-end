import os

# APP CONFIG
VALID_APP_ENVIRONMENTS = ['development', 'staging', 'production']
DB_CONNECTION_STRING = os.getenv('DB_CONNECTION', 'mysql+pymysql://kickin:kickin@localhost/media_backend')

# CORS
CORS_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS').split(",")

# JWT
JWT_KEY_CERTIFICATE = os.getenv('JWT_KEY_CERTIFICATE').replace(r'\n', '\n')
JWT_AUDIENCE = os.getenv('JWT_AUDIENCE')

# S3 CONFIGURATION
S3_BUCKET = os.getenv('S3_PHOTO_BUCKET')
S3_BUCKET_UPLOAD_PATH = "uploads"
S3_BUCKET_ORIGINAL_PATH = "originals"
S3_BUCKET_PHOTO_PATH = "photos"
S3_UPLOAD_EXPIRY = 15 * 60  # Upload link is valid for 15 minutes.
S3_PHOTO_HOSTNAME = os.getenv('S3_PHOTO_HOSTNAME', 'http://replace.me')
