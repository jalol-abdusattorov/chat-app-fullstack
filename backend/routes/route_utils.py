from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from db import users_collection, messages_collection, room_members_collection, rooms_collection

swagger_bearer_scheme = HTTPBearer(auto_error=False)


def check_owner(request: Request, user_id: str):
    if request.state.user.get('uid') != user_id:
        raise HTTPException(status_code=403, detail="Permission denied, not the owner of the account")

def has_user_joined_the_room(user_id: str, room_id: str) -> bool:
    return room_members_collection.find_one(
        { "room_id": ObjectId(room_id), "user_id": ObjectId(user_id) },
        { "_id": 1} ,
    ) is not None

def get_room_last_message(room_id: ObjectId, user_id: ObjectId):
    if type(room_id) == str:
        try:
            room_id = ObjectId(room_id)
        except bson.errors.InvalidId:
            raise HTTPException(status_code=403, detail="invalid id")

    last_messages = list(messages_collection.find({ 'room_id': room_id, 'deleted': False }, { "_id": 0, "body": 1, "created_at": 1, "sender_id": 1 } ).sort('seq', -1).limit(1))
    if not last_messages:
        return None
    last_messages = last_messages[0]

    if last_messages['sender_id'] == user_id:
        last_messages['display_name'] = 'you'
    else:
        user = users_collection.find_one({ "_id": last_messages['sender_id'] }, { "display_name": 1 })
        last_messages['display_name'] = user['display_name']

    last_messages['sender_id'] = str(last_messages['sender_id'])

    return last_messages

def get_rooms_last_message_seq(room_id: ObjectId):
    if type(room_id) == str:
        try:
            room_id = ObjectId(room_id)
        except bson.errors.InvalidId:
            raise HTTPException(status_code=403, detail="invalid id")

    last_messages = list(messages_collection.find({ 'room_id': room_id, 'deleted': False }, { "_id": 0, "seq": 1 } ).sort('seq', -1).limit(1))

    if not last_messages:
        return 0

    return last_messages[0]['seq']

def count_user_unread_messages(rid: ObjectId, uid: ObjectId) -> int:
    room = rooms_collection.find_one({ "_id": rid }, { "last_seq": 1 })
    member = room_members_collection.find_one(
        { "room_id": rid, "user_id": uid },
        { "last_read_seq": 1 },
    )
    if not room or not member:
        raise HTTPException(status_code=404, detail="Room member not found")
    return room["last_seq"] - member["last_read_seq"]

def mark_read(rid: ObjectId, uid: ObjectId, seq: int) -> None:
    room_members_collection.update_one(
        { "room_id": rid, "user_id": uid },
        { "$max": { "last_read_seq": seq } },
    )
