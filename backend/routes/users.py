import bson
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from datetime import datetime as dt, timezone

from models import UsersRequest
from db import users_collection, privates_collection, groups_collection, messages_collection


invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
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
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": user_id })
    if not user:
        return {'message': "user does not exist"}

    user['_id'] = str(user['_id'])
    if len(user['joined_rooms']) > 0:
        for i in range(len(user['joined_rooms'])):
            user['joined_rooms'][i] = str(user['joined_rooms'][i])

    return user


@router.delete('/users/leave-private/{room_id}')
def leave_private_chat(
    room_id: str,
    user_id: str
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)

        room = privates_collection.find_one({ "_id": room_id })
        user = users_collection.find_one({ "_id": user_id })
        if not room:
            raise HTTPException(status_code=403, detail="Room not found")
        if not user:
            raise HTTPException(status_code=403, detail="User not found")

        user1 = room['members'][0]
        user2 = room['members'][1]
        if user1 != user_id and user2 != user_id:
            raise HTTPException(status_code=403, detail="Cannot leave private chat for others")

        users_collection.update_one({ "_id": user1 }, { "$pull": { "joined_rooms": room_id } })
        users_collection.update_one({ "_id": user2 }, { "$pull": { "joined_rooms": room_id } })
        privates_collection.delete_one({ "_id": room_id })
        messages_collection.delete_many({ "room_id": room_id })

        return {"message": "Success"}

    except bson.errors.InvalidId:
        raise invalid_id_exception

@router.delete('/users/leave-group/{room_id}')
def leave_group_chat(
    room_id: str,
    user_id: str
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)

        user = users_collection.find_one({ "_id": user_id })
        room = groups_collection.find_one({ "_id": room_id })
        room_members = [room_member for room_member in room['members']]

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if user_id not in room_members:
            raise HTTPException(status_code=403, detail="User hasn't joined the room")

        if room.get('owner') == user_id:
            for i in room['members']:
                i = ObjectId(i)
                users_collection.update_one({ "_id": i }, { "$pull": { "joined_rooms": room_id } })

            groups_collection.delete_one({ "_id": room_id })
            messages_collection.delete_many({ "room_id": room_id })

        users_collection.update_one({ "_id": user_id }, { "$pull": { "joined_rooms": room_id } })
        groups_collection.update_one({ "_id": room_id }, { "$pull": { "members": user_id } })

        return {"message": "Success"}

    except bson.errors.InvalidId:
        raise invalid_id_exception
