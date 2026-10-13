from datetime import datetime as dt, timezone
from typing import Annotated
import bson
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from auth.services.auth_service import get_current_user_id
from routes.route_utils import check_owner, has_user_joined_the_room
from db import messages_collection, users_collection, room_members_collection, rooms_collection
from routes.rooms import swagger_bearer_scheme, is_user_in_room
from routes.rooms import manager

invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
room_not_found_exception = HTTPException(status_code=404, detail="Room not found")
user_not_found_exception = HTTPException(status_code=404, detail="User not found")
router = APIRouter()

def serialize_message(m: dict) -> dict:
    deleted = m.get("deleted", False)
    return {
        "id": str(m["_id"]),
        "room_id": str(m["room_id"]),
        "sender_id": str(m["sender_id"]),
        "seq": m["seq"],
        "body": None if deleted else m.get("body"),
        "created_at": m["created_at"].isoformat(),
        "edited_at": m["edited_at"].isoformat() if m.get("edited_at") else None,
        "deleted": deleted,
    }

def get_users_map(sender_ids: set[ObjectId]) -> dict:
    ids = list(sender_ids)
    if not sender_ids:
        return {}
    users = users_collection.find(
        { '_id': { '$in': ids } },
        { 'username': 1, 'display_name': 1 }
    )
    return {u['_id']: u for u in users}

def serialize_with_sender(m: dict, users_map: dict) -> dict:
    base = serialize_message(m)
    base.pop("sender_id", None)

    u = users_map.get(m['sender_id'])
    base['sender'] = {
        'id': str(m["sender_id"]),
        'username': u.get('username') if u else None,
        'display_name': u.get('display_name') if u else "Deleted user",
    }
    return base


# AUTHORIZED AND
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

    # if not is_user_in_room(user_id, room_id):
    #     raise HTTPException(status_code=403, detail="User not in room")

    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    query = {'room_id': rid}
    if before_seq is not None:
        query['seq'] = {"$lt": before_seq}

    docs = list(messages_collection.find(query).sort('seq', -1).limit(limit))

    users_map = get_users_map({ m['sender_id'] for m in docs })

    return {
        "messages": [serialize_with_sender(m, users_map) for m in docs],
        "next_before_seq": docs[-1]['seq'] if len(docs) == limit else None
    }


# AUTHORIZED AND IN ROOM CHECK
@router.put("/messages/edit-message/{message_id}")
async def edit_message(
    message_id: str,
    room_id: str,
    edited_message: str,
    user_id: str = Depends(get_current_user_id),
):
    if not has_user_joined_the_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")
    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    edited_message = edited_message.strip()
    if not edited_message:
        raise HTTPException(status_code=403, detail="Cannot edit message to empty space")

    try:
        mid, rid, uid = ObjectId(message_id), ObjectId(room_id), ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    now = dt.now(timezone.utc)
    result = messages_collection.update_one(
        { "_id": mid, "room_id": rid, "sender_id": uid, "deleted": False },
        { "$set": { "body": edited_message, "edited_at": now } }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=403, detail="Message not found")

    await manager.broadcast_to_room(
        room_id,
        {
            'type': 'message_updated',
            'id': message_id,
            'room_id': room_id,
            'body': edited_message,
            'edited_at': now.isoformat(),
        }
    )
    return {'ok': True}

# AUTHORIZED AND IN ROOM CHECK
@router.delete("/messages/delete-message/{message_id}")
async def delete_message(
    message_id: str,
    room_id: str,
    user_id: str = Depends(get_current_user_id),
):
    if not has_user_joined_the_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")
    if not is_user_in_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User not in room")

    try:
        rid, mid, uid = ObjectId(room_id), ObjectId(message_id), ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room = rooms_collection.find_one({ "_id": rid }, { 'owner_id': 1 })
    if not room:
        raise room_not_found_exception

    message = messages_collection.find_one({ "room_id": rid, "_id": mid })
    if not message:
        raise HTTPException(status_code=403, detail="Message not found")
    if uid != message['sender_id'] and uid != room.get('owner_id'):
        raise HTTPException(status_code=403, detail='Cannot delete others messages')

    result = messages_collection.update_one(
        { "_id": mid, "room_id": rid, "sender_id": uid, "deleted": False },
        { "$set": { "deleted": True, "body": None }},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    await manager.broadcast_to_room(room_id, {
        "type": "message_deleted",
        "id": message_id,
        "room_id": room_id,
    })

    return {"ok": True}

    # updated = messages_collection.update_one({ "room_id": rid, "_id": mid }, { "$set": { "deleted": True } }).modified_count
    # if updated != 0:
    #     return {
    #         'status': 'deleted',
    #         'deleted_docs': updated
    #     }

    # raise HTTPException(status_code=404, detail="Message not found")
