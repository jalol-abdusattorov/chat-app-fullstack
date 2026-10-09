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
from db import users_collection, rooms_collection, messages_collection
from routes.route_utils import check_owner, swagger_bearer_scheme

    
invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
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


# # AUTHOIRZED AND OWNER CHECK
# @router.delete('/users/leave-private/{room_id}')
# def leave_private_chat(
#     room_id: str,
#     user_id: str,
#     request: Request,
#     _: Annotated[str, Depends(swagger_bearer_scheme)]
# ):
#     check_owner(request, user_id)
#     try:
#         room_id = ObjectId(room_id)
#         user_id = ObjectId(user_id)

#         room = privates_collection.find_one({ "_id": room_id })
#         user = users_collection.find_one({ "_id": user_id })
#         if not room:
#             raise HTTPException(status_code=403, detail="Room not found")
#         if not user:
#             raise HTTPException(status_code=403, detail="User not found")

#         user1 = room['members'][0]
#         user2 = room['members'][1]
#         if user1 != user_id and user2 != user_id:
#             raise HTTPException(status_code=403, detail="Cannot leave private chat for others")

#         users_collection.update_one({ "_id": user1 }, { "$pull": { "joined_rooms": room_id } })
#         users_collection.update_one({ "_id": user2 }, { "$pull": { "joined_rooms": room_id } })
#         privates_collection.delete_one({ "_id": room_id })
#         messages_collection.delete_many({ "room_id": room_id })

#         return {"message": "Success"}

#     except bson.errors.InvalidId:
#         raise invalid_id_exception


# # AUTHOIRZED AND OWNER CHECK
# @router.delete('/users/leave-group/{room_id}')
# def leave_group_chat(
#     room_id: str,
#     user_id: str,
#     request: Request,
#     _: Annotated[str, Depends(swagger_bearer_scheme)]
# ):
#     check_owner(request, user_id)
#     try:
#         room_id = ObjectId(room_id)
#         user_id = ObjectId(user_id)

#         user = users_collection.find_one({ "_id": user_id })
#         room = groups_collection.find_one({ "_id": room_id })
#         room_members = [room_member for room_member in room['members']]

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         if not room:
#             raise HTTPException(status_code=404, detail="Room not found")

#         if user_id not in room_members:
#             raise HTTPException(status_code=403, detail="User hasn't joined the room")

#         if room.get('owner') == user_id:
#             for i in room['members']:
#                 i = ObjectId(i)
#                 users_collection.update_one({ "_id": i }, { "$pull": { "joined_rooms": room_id } })

#             groups_collection.delete_one({ "_id": room_id })
#             messages_collection.delete_many({ "room_id": room_id })

#         users_collection.update_one({ "_id": user_id }, { "$pull": { "joined_rooms": room_id } })
#         groups_collection.update_one({ "_id": room_id }, { "$pull": { "members": user_id } })

#         return {"message": "Success"}

#     except bson.errors.InvalidId:
#         raise invalid_id_exception
