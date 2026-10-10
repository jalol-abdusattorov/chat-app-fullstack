from datetime import datetime as dt, timezone
from typing import Annotated
import bson
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from routes.route_utils import has_user_joined_the_room, check_owner
from db import messages_collection, users_collection, room_members_collection, rooms_collection
from routes.rooms import swagger_bearer_scheme, is_user_in_room


invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
room_not_found_exception = HTTPException(status_code=404, detail="Room not found")
user_not_found_exception = HTTPException(status_code=404, detail="User not found")
router = APIRouter()

def serialize_message(msg: dict):
    deleted = msg.get("deleted", False)
    return {
        "id": str(msg['_id']),
        "room_id": str(msg['room_id']),
        "sender_id": str(msg['sender_id']),
        "seq": msg['seq'],
        "body": None if deleted else msg['body'],
        "created_at": msg['created_at'].isoformat(),
        "edited_at": msg['edited_at'].isoformat() if msg['edited_at'] else None,
        "deleted": deleted
    }

# AUTHORIZED AND IN ROOM CHECK
@router.get("/room/{room_id}/messages")
def get_room_messages(
    room_id: str,
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)],
    limit: int = Query(50, ge=1, le=100),
    before_seq: int | None = None,
):
    check_owner(request, user_id)

    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")
    
    try:
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    query = {'room_id': rid}
    if before_seq is not None:
        query['seq'] = {"$lt": before_seq}

    docs = list(messages_collection.find(query).sort('seq', -1).limit(limit))
    return {
        "messages": [serialize_message(m) for m in docs],
        "next_before_seq": docs[-1]['seq'] if len(docs) == limit else None
    }


# AUTHORIZED AND IN ROOM CHECK
@router.put("/messages/edit-message/{message_id}")
def edit_message(
    message_id: str,
    room_id: str,
    user_id: str,
    edited_message: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    edited_message = edited_message.strip()
    if not edited_message:
        raise HTTPException(status_code=403, detail="Cannot edit message to empty space")

    try:
        mid = ObjectId(message_id)
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    member = room_members_collection.find_one({ "room_id": rid, "user_id": uid })
    if not member:
        raise HTTPException(status_code=404, detail="User isn't a member")

    message = messages_collection.find_one({ "_id": mid }, { "deleted": 1 })
    if message['deleted']:
        raise HTTPException(status_code=403, detail="Message is deleted")

    now = dt.now(timezone.utc)
    updated = messages_collection.update_one({ "_id": mid }, { "$set": { "edited_at": now, "body": edited_message } }).modified_count
    if updated:
        return {
            'status': 'updated',
            'edited_to': edited_message
        }

    raise HTTPException(status_code=404, detail="Message not found")


# AUTHORIZED AND IN ROOM CHECK
@router.delete("/messages/delete-message/{message_id}")
def delete_message(
    message_id: str,
    room_id: str,
    user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    try:
        rid = ObjectId(room_id)
        mid = ObjectId(message_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room = rooms_collection.find_one({ "_id": rid })
    if not room:
        raise room_not_found_exception

    updated = messages_collection.update_one({ "_id": mid }, { "$set": { "deleted": True } }).modified_count
    if updated != 0:
        return {
            'status': 'deleted',
            'deleted_docs': updated
        }

    raise HTTPException(status_code=404, detail="Message could be deleted")

    # # Get Message
    # message = messages_collection.find_one({ "_id": message_id })
    # if not message:
    #     raise HTTPException(status_code=404, detail="Message not found")

    # if user_id != message['sender_id']:
    #     raise HTTPException(status_code=403, detail="Cannot delete others message")

    # # Get room
    # room = privates_collection.find_one({ "_id": room_id })
    # room_type = 'private'
    # if not room:
    #     room = groups_collection.find_one({ "_id": room_id })
    #     room_type = 'group'
    # if not room:
    #     raise room_not_found_exception

    # # Get user
    # user = users_collection.find_one({ "_id": user_id })
    # if not user:
    #     raise user_not_found_exception
    # if not has_user_joined_the_room(user_id, room_id, room_type):
    #     raise HTTPException(status_code=403, detail="User hasn't joined the room")


    # deleted_count = messages_collection.delete_one({ "_id": message_id }).deleted_count
    # if deleted_count != 0:
    #     return {'message': 'Deleted the message successfuly'}

    # return {'message': "Coudn't delete the message for some reason"}
