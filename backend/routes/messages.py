import bson
from bson import ObjectId
from fastapi import APIRouter, HTTPException

from db import messages_collection, users_collection, privates_collection, groups_collection


router = APIRouter()

@router.get("/room/{room_id}/messages")
def get_room_messages(
    room_id: str,
    user_id: str,
    page: int,
    room_type: str | None = None
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=403, detail="invalid id")

    user = users_collection.find_one({ "_id": user_id })
    if room_type == 'private':
        room = privates_collection.find_one({ "_id": room_id })
    elif room_type == 'group':
        room = groups_collection.find_one({ "_id": room_id })
    else:
        room = privates_collection.find_one({ "_id": room_id })
        if not room:
            room = groups_collection.find_one({ "_id": room_id })

    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    if not room:
        raise HTTPException(status_code=404, detail="room not found")

    for user_room in user['joined_rooms']:
        if user_room == room_id:
            break
    else:
        raise HTTPException(status_code=403, detail="User hasn't joined the room")

    if page <= 0:
        raise HTTPException(status_code=403, detail="Page should be greater than 0")

    skipping_val = (page - 1) * 100
    limit = 100

    messages = messages_collection.find({ "room_id": room_id }).skip(skipping_val).limit(limit).to_list(100)

    if not messages:
        return {'message': "Chat/Page is empty"}

    for i in range(len(messages)):
        messages[i]['_id'] = str(messages[i]['_id'])
        messages[i]['room_id'] = str(messages[i]['room_id'])
        messages[i]['sender_id'] = str(messages[i]['sender_id'])

    return messages
