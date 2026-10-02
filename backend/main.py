from fastapi import FastAPI

from routes.users import router as users_router
from routes.rooms import router as rooms_router

app = FastAPI()

@app.get("/")
def homepage():
    return {"message": "homepage"}


app.include_router(users_router, tags=['Users'])
app.include_router(rooms_router, tags=['Rooms'])