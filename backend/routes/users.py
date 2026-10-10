from random import choice
import re
import bson
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime as dt, timedelta, timezone

from auth.utils.auth_utils import get_password_hash
from auth.services.auth_service import create_access_token
from auth.models.token import Token
from routes.rooms import is_user_online_check
from models import UsersRequest
from db import users_collection, rooms_collection, messages_collection, room_members_collection
from routes.route_utils import check_owner, swagger_bearer_scheme


invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
room_not_found_exception = HTTPException(status_code=404, detail="Room not found")
user_not_found_exception = HTTPException(status_code=404, detail="User not found")
router = APIRouter()

# NO AUTH
@router.post('/users')
def create_account(
    user: UsersRequest
):
    if len(user.password) > 72: raise HTTPException(status_code=403, detail="password is too long")

    is_unique_username = users_collection.find_one({ "username": user.username })
    if is_unique_username:
        raise HTTPException(status_code=403, detail=f"Username is already used")

    is_unique_email = users_collection.find_one({ "email": user.email })
    if is_unique_email:
        raise HTTPException(status_code=403, detail=f"Email is already used by '{is_unique_email['username']}'")

    new_user = {
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "bio": user.bio,
        "password_hash": get_password_hash(user.password),
        "created_at": dt.now(timezone.utc),
    }

    inserted_id = users_collection.insert_one(new_user).inserted_id

    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={'sub': new_user['email'], 'uid': str(inserted_id)},
        expires_delta=access_token_expires
    )

    return {'user_id': str(inserted_id), 'token': Token(access_token=access_token, token_type='bearer')}


# AUTHOIRZED
@router.get('/users/{user_id}')
def get_user(
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    try:
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": user_id })
    if not user:
        return {'message': "user does not exist"}

    user['_id'] = str(user['_id'])
    del user['password_hash']

    return user


# AUTHORIZED
@router.get("/users/search/{username}")
def search_user_by_username(
    username: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    # "Removes" some of the punctuations in order to not crash MongoDB
    clean_username = re.escape(username.strip())

    cursor = users_collection.find({
        "$or": [
            {
                "username": clean_username
            },
            {
                "username": {
                    "$regex": clean_username,
                    "$options": "i"
                }
            }
        ]
    })
    result = list(cursor)

    for doc in result:
        doc['_id'] = str(doc['_id'])
        del doc['email']
        del doc['password_hash']
        del doc['joined_rooms']

    return {"result": result}


# AUTHORIZED
@router.get("/users/is-online/{user_id}")
def is_user_online(
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    try:
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": user_id })
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return is_user_online_check(str(user_id))


# AUTHOIRZED AND OWNER CHECK
@router.delete('/users/leave-private/{room_id}')
def leave_private_chat(
    room_id: str,
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room_deleted = rooms_collection.delete_one({ "_id": rid }).deleted_count
    if room_deleted == 0:
        raise room_not_found_exception

    deleted = room_members_collection.delete_many({ "room_id": rid }).deleted_count
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Member not found")

    return {
        'status': 'deleted',
        'message': f'left private chat, removed {deleted} members, and deleted {room_deleted} room'
    }


# AUTHOIRZED AND OWNER CHECK
@router.delete('/users/leave-group/{room_id}')
def leave_group_chat(
    room_id: str,
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    member = room_members_collection.find_one({ "room_id": rid, "user_id": uid }, { '_id': 0, 'role': 1, 'user_id': 1 })
    if not member:
        raise HTTPException(status_code=403, detail="Room not found or Member not found")
    room_members = list(room_members_collection.find({ "room_id": rid }, { "_id": 0, 'role': 1, 'user_id': 1 }))
    members_count = len(room_members)

    # If the owner is leaving one of the ADMINS will be new owner or it'll be randomly selected (any member)
    room_members = [i for i in room_members if i != member]
    if member.get('role') == 'owner':

        if members_count > 1:
            is_there_admin = False
            for i in room_members:
                if i.get('role') == 'admin':
                    is_there_admin = True
                    break

            if is_there_admin:
                room_members = [j for j in room_members if j.get('role') == 'admin']
            
            new_owner = choice(room_members)
            room_members_collection.update_one({ "room_id": rid, "user_id": ObjectId(new_owner['user_id']) }, { "$set": { "role": "owner" } })

    room_members_collection.delete_one({ "room_id": rid, "user_id": uid })

    if members_count == 1:
        rooms_collection.delete_one({ "_id": rid })

    return {
        'status': 'deleted',
        'message': 'successfuly left the group'
    }
