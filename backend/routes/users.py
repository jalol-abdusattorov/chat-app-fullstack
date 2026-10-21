from random import choice
import re
import bson
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from datetime import datetime as dt, timedelta, timezone

from auth.utils.auth_utils import get_password_hash
from auth.services.auth_service import create_access_token, get_current_user_id
from auth.models.token import Token
from routes.rooms import is_user_online_check
from models import UsersRequest
from db import users_collection, rooms_collection, room_members_collection, messages_collection
from routes.route_utils import check_owner, count_user_unread_messages, has_user_joined_the_room, mark_read, swagger_bearer_scheme, get_room_last_message


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
        data={'sub': str(inserted_id), 'email': new_user['email']},
        expires_delta=access_token_expires
    )

    return {'user_id': str(inserted_id), 'token': Token(access_token=access_token, token_type='bearer')}


# AUTHORIZED
@router.get("/users/get-user-rooms")
def get_user_rooms(
    user_id: str = Depends(get_current_user_id),
):
    try:
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    memberships = list(room_members_collection.find(
        { "user_id": uid },
        { "_id": 0, "room_id": 1, "last_read_seq": 1 },
    ))
    if not memberships:
        return {"rooms": []}

    room_ids = [m["room_id"] for m in memberships]

    rooms = {}
    for room in rooms_collection.aggregate([
        {
            "$match": {
                "_id": { "$in": room_ids }
            }
        },
        {
            "$project": { "type": 1, "name": 1, "last_seq": 1 }
        },
        {
            "$lookup": {
                "from": messages_collection.name,
                "let": { "rid": "$_id" },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    { "$eq": [ "$room_id", "$$rid" ] },
                                    { "$eq": [ "$deleted", False ] },
                                ]
                            }
                        }
                    },
                    { "$sort": { "seq": -1 } },
                    { "$limit": 1 },
                    { "$project": { "_id": 0, "body": 1, "created_at": 1, "sender_id": 1 } },
                ],
                "as": "last_message",
            }
        },
    ]):
        rooms[room["_id"]] = room

    private_ids = [rid for rid, r in rooms.items() if r["type"] == "private"]
    other_user_of = {}
    if private_ids:
        for m in room_members_collection.find(
            { "room_id": { "$in": private_ids }, "user_id": { "$ne": uid } },
            { "_id": 0, "room_id": 1, "user_id": 1 },
        ):
            other_user_of[m["room_id"]] = m["user_id"]

    needed_user_ids = set(other_user_of.values())
    for r in rooms.values():
        if r["last_message"]:
            needed_user_ids.add(r["last_message"][0]["sender_id"])

    names = {}
    if needed_user_ids:
        names = {
            u["_id"]: u["display_name"]
            for u in users_collection.find(
                { "_id": { "$in": list(needed_user_ids) } },
                { "display_name": 1 },
            )
        }

    result = []
    for m in memberships:
        room = rooms.get(m["room_id"])
        if room is None:
            continue

        if room["type"] == "private":
            name = names.get(other_user_of.get(m["room_id"]))
        else:
            name = room["name"]

        last_message = None
        if room["last_message"]:
            lm = room["last_message"][0]
            lm["display_name"] = "you" if lm["sender_id"] == uid else names.get(lm["sender_id"])
            lm["sender_id"] = str(lm["sender_id"])
            last_message = lm

        result.append({
            "room_id": str(m["room_id"]),
            "type": room['type'],
            "name": name,
            "last_message": last_message,
            "unread_count": room["last_seq"] - m["last_read_seq"],
        })

    return {"rooms": result, "ok": True}


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
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": uid }, { "display_name": 1 })
    if not user:
        raise user_not_found_exception

    return {
        'user_id': user_id,
        'display_name': user['display_name']
    }


# AUTHORIZED AND IN ROOM CHECK
@router.put("/users/read-messages")
def read_messages(
    room_id: str,
    seq: int = Query(gt=0),
    user_id: str = Depends(get_current_user_id),
):
    try:
        uid = ObjectId(user_id)
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    if not has_user_joined_the_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")

    room = rooms_collection.find_one({ "_id": rid }, { "last_seq": 1 })
    if not room:
        raise room_not_found_exception

    seq = min(seq, room['last_seq'])

    unread_msgs_before = count_user_unread_messages(rid, uid)
    mark_read(rid, uid, seq)
    unread_msgs = count_user_unread_messages(rid, uid)

    return {
        'read_messages_count': unread_msgs_before - unread_msgs,
        'ok': True
    }


# AUTHORIZED
@router.get("/users/search/{username}")
def search_user_by_username(
    username: str,
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        current_uid = ObjectId(current_user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    # "Removes" some of the punctuations in order to not crash MongoDB (e.g. user types "bo@b" -> "bo\@b")
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
                },
                "_id": {
                    "$ne": current_uid
                }
            }
        ]
    })
    result = list(cursor)

    for doc in result:
        doc['_id'] = str(doc['_id'])
        del doc['email']
        del doc['password_hash']

    # print(result)
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
    user_id: str = Depends(get_current_user_id),
):
    try:
        rid = ObjectId(room_id)
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
    user_id: str = Depends(get_current_user_id),
):
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
