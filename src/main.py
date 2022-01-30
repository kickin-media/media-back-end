import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

import variables
from routers import events, albums, photos, author

from tasks.process_uploaded_photo import task as process_uploaded_photo

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
    allow_origins=variables.CORS_ORIGINS[app_environment],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] if app_environment == 'development' else []
)

# Include routers
api.include_router(events.router)
api.include_router(albums.router)
api.include_router(photos.router)
api.include_router(author.router)


# Set-up tasks
@api.on_event('startup')
@repeat_every(seconds=30, wait_first=False, raise_exceptions=True)
def process_uploaded_photo_task():
    process_uploaded_photo()
