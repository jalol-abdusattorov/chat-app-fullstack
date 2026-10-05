import os
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from routes.users import router as users_router
from routes.rooms import router as rooms_router
from routes.messages import router as messages_router
from auth.routes.auth_router import auth_router


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
public_endpoints = ["/docs", "/openapi.json", "/api/auth/login", "/users", "/"]

open_api_tags = [
    {
        "name": "Users",
        "description": "User operations"
    },
    {
        "name": "Auth",
        "description": "Authorization"
    },
    {
        "name": "Rooms",
        "description": "Room operations"
    },
    {
        "name": "Messages",
        "description": "Messages"
    }
]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Open the public endpoints because they dont need auth
        if request.url.path in public_endpoints:
            return await call_next(request)

        # Get auth header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Not Authorized"})

        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Inject user, token payload and admin status into state for auth 
            request.state.user = payload
            request.state.token_string = token

        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=403, content={"detail": "Token has expired"})
        except jwt.PyJWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)


app = FastAPI(open_api_tags=open_api_tags, title="Chat")
app.add_middleware(AuthMiddleware)

app.include_router(users_router, tags=['Users'])
app.include_router(auth_router, prefix="/api")
app.include_router(rooms_router, tags=['Rooms'])
app.include_router(messages_router, tags=['Messages'])


@app.get("/")
def homepage():
    return {"message": "homepage"}
