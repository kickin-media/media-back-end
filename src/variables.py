import os

VALID_APP_ENVIRONMENTS = ['development', 'staging', 'production']

DB_CONNECTION_STRING = os.getenv('DB_CONNECTION', 'mysql+pymysql://kickin:kickin@localhost/media_backend')

CORS_ORIGINS = {
    'production': [],
    'staging': [],
    'development': ['http://localhost:3000'],
}

# These values are asymmetric public values that are related to the Media Tool Auth0 client.
# For now these are hardcoded, but abstracted here so we can easily move them to environment variables.
JWT_KEY_CERTIFICATE = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxY8r4V7BVBXaSIhfky+j
RLI1RFaUj1PvFGfVA34rj+Z5xfpg1zkP47W/KNN/EB/rllRa0rn4py6ygbSuvSby
ZnKNhypaDkjURZwMbwCJyxN0BREHjMTjwn0GVkYkWvMY9iQ9mCwN+oLz8C/4ZLxP
mDp3pSh765F2+sNylJ4Lk2b11WTVf7QSCQjQ8Kf2Yj3zKna9/OiONLP8y5EI9n54
anLLMypZZV0Zhx7ou6RJDWgBgBDuNigILr9HWp5G9xCooqIdmNh3hZpAeDBhMNfj
7HRLo1iixm+uYA9tUsEuZyQfz/CwrTHOMYx9xtzeQhjiNk135chpMIqDR3R2n5g+
LwIDAQAB
-----END PUBLIC KEY-----"""
JWT_AUDIENCE = "https://api.kick-in.media"
