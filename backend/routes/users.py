from random import choice
import re
import bson
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from datetime import datetime as dt, timedelta, timezone

from auth.utils.auth_utils import get_password_hash
from auth.services.auth_service import create_access_token
from auth.models.token import Token
from routes.rooms import is_user_in_room, is_user_online_check
from models import UsersRequest
from db import users_collection, rooms_collection, messages_collection, room_members_collection
from routes.route_utils import check_owner, count_user_unread_messages, mark_read, swagger_bearer_scheme, get_room_last_message


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
@router.get("/users/{user_id}/display_name")
def get_user_username(
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    try:
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": uid }, { "display_name": 1 })

    return {
        'user_id': user_id,
        'display_name': user['display_name']
    }


# AUTHORIZED
@router.get("/users/get-user-rooms/{user_id}")
def get_user_rooms(
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)],
):
    check_owner(request, user_id)

    try:
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user_joined_rooms = list(room_members_collection.find({ "user_id": uid }, { "_id": 0, "room_id": 1 }))

    for dct in user_joined_rooms:
        room = rooms_collection.find_one({ "_id": dct['room_id'] }, { "type": 1, "name": 1 })
        
        if room['type'] == 'private':
            members = list(room_members_collection.find({ "room_id": dct['room_id'] }))
            other_user = members[0]['user_id']
            if members[0]['user_id'] == uid:
                other_user = members[1]['user_id']

            dct['name'] = users_collection.find_one({ "_id": other_user }, { 'display_name': 1 })['display_name']
        else:
            dct['name'] = room['name']

        dct['last_message'] = get_room_last_message(dct['room_id'])
        dct['unread_count'] = count_user_unread_messages(dct['room_id'], uid)
        dct['room_id'] = str(dct['room_id'])

    return {'rooms': user_joined_rooms}


# AUTHORIZED AND IN ROOM CHECK
@router.put("/users/read-messages/{user_id}")
def read_messages(
    user_id: str,
    room_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)],
    seq: int = Query(gt=0),
):
    check_owner(request, user_id)

    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    try:
        uid = ObjectId(user_id)
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    unread_msgs_before = count_user_unread_messages(rid, uid)
    mark_read(rid, uid, seq)
    unread_msgs = count_user_unread_messages(rid, uid)

    return {
        'read_messages_count': unread_msgs_before - unread_msgs
    }


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
