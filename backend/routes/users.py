import bson
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from datetime import datetime as dt, timezone

from models import UsersRequest
from db import users_collection

router = APIRouter()

@router.post('/users/register')
def create_account(
    user: UsersRequest
):
    if len(user.password) > 72: raise HTTPException(status_code=403, detail="password is too long")

    is_unique_email = users_collection.find_one({ "email": user.email })
    if is_unique_email:
        raise HTTPException(status_code=403, detail=f"Email is already used by {is_unique_email['name']}")

    new_user = {
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "password_hash": user.password,
        "created_at": dt.now(timezone.utc),
        # ["6ab2...", "6ab3mc.."]
        "joined_rooms": []
    }

    inserted_id = users_collection.insert_one(new_user).inserted_id

    return {'user_id': str(inserted_id)}

@router.get('/users/{user_id}')
def get_user(user_id: str):
    try:
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=403, detail="invalid id")

    user = users_collection.find_one({ "_id": user_id })
    if not user:
        return {'message': "user does not exist"}

    user['_id'] = str(user['_id'])
    if len(user['joined_rooms']) > 0:
        for i in range(len(user['joined_rooms'])):
            user['joined_rooms'][i] = str(user['joined_rooms'][i])

    return user
