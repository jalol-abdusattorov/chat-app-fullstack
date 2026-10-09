from typing import Annotated
import bson
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from routes.route_utils import has_user_joined_the_room
from db import messages_collection, users_collection
from routes.rooms import swagger_bearer_scheme, is_user_in_room


invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
room_not_found_exception = HTTPException(status_code=404, detail="Room not found")
user_not_found_exception = HTTPException(status_code=404, detail="User not found")
router = APIRouter()

# AUTHORIZED AND IN ROOM CHECK
@router.get("/room/{room_id}/messages")
def get_room_messages(
    room_id: str,
    user_id: str,
    page: int,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)],\
):
    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": user_id })
    room = privates_collection.find_one({ "_id": room_id })
    if not room:
        room = groups_collection.find_one({ "_id": room_id })

    if not user:
        raise user_not_found_exception
    if not room:
        raise room_not_found_exception

    for user_room in user['joined_rooms']:
        if user_room == room_id:
            break
    else:
        raise HTTPException(status_code=403, detail="User hasn't joined the room")

    if page <= 0:
        raise HTTPException(status_code=403, detail="Page should be greater than 0")

    skipping_val = (page - 1) * 100
    limit = 100

    messages = messages_collection.find({ "room_id": room_id }).sort("created_at", -1).skip(skipping_val).limit(limit).to_list(100)

    if not messages:
        return {'message': "Chat/Page is empty"}

    for i in range(len(messages)):
        messages[i]['_id'] = str(messages[i]['_id'])
        messages[i]['room_id'] = str(messages[i]['room_id'])
        messages[i]['sender_id'] = str(messages[i]['sender_id'])

    return messages


# AUTHORIZED AND IN ROOM CHECK
@router.put("/messages/edit-message/{message_id}")
def edit_message(
    message_id: str,
    room_id: str,
    user_id: str,
    editing_message: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    editing_message = editing_message.strip()
    if not editing_message:
        raise HTTPException(status_code=403, detail="Cannot edit message to empty space")

    try:
        message_id = ObjectId(message_id)
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    # Get room
    room = privates_collection.find_one({ "_id": room_id })
    if not room:
        groups_collection.find_one({ "_id": room_id })

    if not room:
        raise room_not_found_exception

    # Get user
    user = users_collection.find_one({ "_id": user_id })
    if not user:
        raise user_not_found_exception

    # Edit the original message
    result = messages_collection.update_one({ "_id": message_id }, { "$set": { "data": editing_message, "edited": True } })
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    return {'message': "Edited message successfuly"}


# AUTHORIZED AND IN ROOM CHECK
@router.delete("/messages/delete-message/{message_id}")
def delete_message(
    message_id: str,
    room_id: str,
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)
        message_id = ObjectId(message_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    # Get Message
    message = messages_collection.find_one({ "_id": message_id })
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if user_id != message['sender_id']:
        raise HTTPException(status_code=403, detail="Cannot delete others message")

    # Get room
    room = privates_collection.find_one({ "_id": room_id })
    room_type = 'private'
    if not room:
        room = groups_collection.find_one({ "_id": room_id })
        room_type = 'group'
    if not room:
        raise room_not_found_exception

    # Get user
    user = users_collection.find_one({ "_id": user_id })
    if not user:
        raise user_not_found_exception
    if not has_user_joined_the_room(user_id, room_id, room_type):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")


    deleted_count = messages_collection.delete_one({ "_id": message_id }).deleted_count
    if deleted_count != 0:
        return {'message': 'Deleted the message successfuly'}

    return {'message': "Coudn't delete the message for some reason"}
