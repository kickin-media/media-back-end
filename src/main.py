import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import variables
from routers import events, albums, photos, author


app_environment = os.getenv('ENVIRONMENT', None)
if app_environment is None:
    raise Exception("You need to specify an ENVIRONMENT environment variable to start the API.")
if app_environment not in variables.VALID_APP_ENVIRONMENTS:
    raise Exception("Invalid ENVIRONMENT value {}, must be one of: {}".format(app_environment, ", ".join(
        variables.VALID_APP_ENVIRONMENTS)))

api = FastAPI()

# Add CORS middleware
api.add_middleware(
    CORSMiddleware,
    allow_origins=variables.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
api.include_router(events.router)
api.include_router(albums.router)
api.include_router(photos.router)
api.include_router(author.router)
