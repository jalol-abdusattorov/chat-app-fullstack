# from datetime import datetime as dt, timezone
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from db import users_collection, messages_collection, room_members_collection


swagger_bearer_scheme = HTTPBearer(auto_error=False)

def check_owner(request: Request, user_id: str):
    if request.state.user.get('uid') != user_id:
        raise HTTPException(status_code=403, detail="Permission denied, not the owner of the account")

def has_user_joined_the_room(user_id: ObjectId, room_id: ObjectId, room_type: str):
    if room_type == 'private':
        room = ....find_one({ "_id": room_id })
    elif room_type == 'group':
        room = ....find_one({ "_id": room_id })

    if user_id in room.get('members', []):
        return True

    return False

def get_room_last_message(room_id: ObjectId):
    if type(room_id) == str:
        try:
            room_id = ObjectId(room_id)
        except bson.errors.InvalidId:
            raise HTTPException(status_code=403, detail="invalid id")

    last_messages = list(messages_collection.find({ 'room_id': room_id, 'deleted': False }, { "_id": 0, "body": 1, "created_at": 1, "sender_id": 1 } ).sort('seq', -1).limit(1))
    if not last_messages:
        return None
    last_messages = last_messages[0]

    user = users_collection.find_one({ "_id": last_messages['sender_id'] }, { "display_name": 1 })
    last_messages['sender_id'] = str(last_messages['sender_id'])
    last_messages['display_name'] = user['display_name']

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

def count_user_unread_messages(room_id: ObjectId, user_id: ObjectId):
    room_last_seq = get_rooms_last_message_seq(room_id)
    room_member = room_members_collection.find_one({ "room_id": room_id, "user_id": user_id }, { "_id": 0, "last_read_seq": 1 })
    if not room_member:
        raise HTTPException(status_code=404, detail="Room member not found")

    return room_last_seq - room_member['last_read_seq']

def mark_read(room_id: ObjectId, user_id: ObjectId, seq: int):
    room_members_collection.update_one(
        { "room_id": room_id, "user_id": user_id },
        { "$max": { "last_read_seq": seq } }
    )