from fastapi import FastAPI

from routers import events, albums

api = FastAPI()

api.include_router(events.router)
api.include_router(albums.router)
