import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import events, albums

api = FastAPI()

# Add CORS headers to the responses of the API
origins = {
    'production': [],
    'staging': [],
    'development': ['http://localhost:3000'],
}[os.getenv('ENVIRONMENT', 'production')]
api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] if os.getenv('ENVIRONMENT', 'production') == 'development' else []
)

# Include routers
api.include_router(events.router)
api.include_router(albums.router)
