import re
from typing import Annotated
import bson
from bson import ObjectId
from datetime import datetime as dt, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, WebSocket, WebSocketDisconnect
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth.services.auth_service import get_current_user_id, user_id_from_token
from models import AddUsersRequest, RemoveUsersRequest, RoomRequest
from db import users_collection, rooms_collection, messages_collection, room_members_collection
from routes.route_utils import has_user_joined_the_room, swagger_bearer_scheme, check_owner

invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
room_not_found_exception = HTTPException(status_code=404, detail="Room not found")
user_not_found_exception = HTTPException(status_code=404, detail="User not found")
router = APIRouter()


def is_user_in_room(user_id: str, room_id: str):
    connections = manager.active_connections.get(str(room_id), [])
    if not connections:
        return False

    for i in connections.values():
        if i == user_id:
            return True

    return False

def get_online_users(room_id: str):
    active_users = []
    connections = manager.active_connections.get(str(room_id))
    if connections:
        active_users = list(connections.values())

    return active_users

def is_user_online_check(user_id: str):
    for connections in manager.active_connections.values():
        for _id in connections.values():
            if _id == user_id:
                return True

    return False

def is_user_online_in_room(user_id: str, room_id: str):
    for _id in manager.active_connections.get(room_id, {}).values():
        if _id == user_id:
            return True

    return False

def add_person_to_room(uid: ObjectId, rid: ObjectId, role="member"):
    room = rooms_collection.find_one({ "_id": rid })
    if not room:
        raise room_not_found_exception

    now = dt.now(timezone.utc)
    new_member = {
        "room_id": rid,
        "user_id": uid,
        "role": role,
        "last_read_seq": room['last_seq'],
        "joined_seq": room['last_seq'],
        "joined_at": now
    }

    result = room_members_collection.insert_one(new_member)
    return result

def add_people_to_room(candidate_uids: list[ObjectId], rid: ObjectId):
    room = rooms_collection.find_one({ "_id": rid }, { "type": 1, "last_seq": 1 })
    if not room:
        raise room_not_found_exception
    if room.get('type', '') == 'private':
        raise HTTPException(status_code=403, detail="Cannot invite people to private chat")

    added_uids = []
    tried_uids = []
    bulk_inserts = []

    now = dt.now(timezone.utc)
    for adding_u in candidate_uids:
        user_exists = users_collection.find_one({ "_id": adding_u })
        if not user_exists:
            raise HTTPException(status_code=404, detail=f"User does not exist '{str(adding_u)}'")

        already_member = room_members_collection.find_one({ "room_id": rid, "user_id": adding_u })
        if not already_member:
            added_uids.append(str(adding_u))
            bulk_inserts.append({
                "room_id": rid,
                "user_id": adding_u,
                "role": 'member',
                "last_read_seq": room.get('last_seq'),
                "joined_seq": room.get('last_seq'),
                "joined_at": now
            })
            continue

        tried_uids.append(str(adding_u))

    if bulk_inserts:
        room_members_collection.insert_many(bulk_inserts)

    return {
        'status': 'success',
        'added_uids_count': len(added_uids),
        'tried_uids_count': len(tried_uids),
        'added_uids': added_uids,
        'tried_uids': tried_uids,
    }

def remove_people_from_room(candidate_uids: list[ObjectId], room: dict, rid: ObjectId):
    deleted_uids = []
    tried_uids = []
    bulk_removals = []

    for candidate_uid in candidate_uids:
        user_a_member = room_members_collection.find_one({ "room_id": rid, "user_id": candidate_uid })
        if not user_a_member:
            raise HTTPException(status_code=404, detail=f"User not a member '{str(candidate_uid)}'")

        if user_a_member.get('role', 'member') == 'owner':
            tried_uids.append(str(candidate_uid))
            continue

        deleted_uids.append(str(candidate_uid))
        bulk_removals.append(candidate_uid)

    if bulk_removals:
        res = room_members_collection.delete_many({ "room_id": rid, "user_id": { "$in": bulk_removals } })

    return {
        'status': 'success',
        'deleted_uids_count': len(deleted_uids),
        'tried_uids_count': len(tried_uids),
        'deleted_uids': deleted_uids,
        'tried_uids': tried_uids,
        'deleted_docs': res.deleted_count if bulk_removals else 0
    }


# AUTHORIZED
@router.post("/rooms/create-room")
def create_room(
    room: RoomRequest,
    user_id: str = Depends(get_current_user_id),
):
    room_data = room.model_dump()
    room_data['user_id'] = user_id

    try:
        owner_id = ObjectId(user_id)
        member_ids = [ObjectId(m_id) for m_id in room.room_members]
    except bson.errors.InvalidId:
        raise invalid_id_exception

    if room.room_type not in {"private", "group"}:
        raise HTTPException(status_code=400, detail="Invalid room type")

    # Validate membership.
    if len(member_ids) != len(set(member_ids)):
        raise HTTPException(status_code=400, detail="Duplicate users are not allowed")

    if owner_id not in member_ids:
        raise HTTPException(status_code=400, detail="The room creator must be a member")

    if room.room_type == "private" and len(member_ids) != 2:
        raise HTTPException(status_code=400, detail="A private room must have exactly 2 members")

    existing_users = {
        user['_id']
        for user in users_collection.find(
            { "_id": { "$in": member_ids } },
            { "_id": 1 }
        )
    }

    missing_users = set(member_ids) - existing_users

    if missing_users:
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {', '.join(map(str, missing_users))}"
        )

    # Check whether the room already exists between these users.
    if room.room_type == 'private':
        private_key = ":".join(sorted(str(mid) for mid in member_ids))

        if rooms_collection.find_one({ 'type': 'private', 'private_key': private_key }):
            raise HTTPException(
                status_code=409,
                detail="Private chat already exists"
            )

        new_room = {
            'name': None,
            'description': room.description,
            'type': room.room_type,
            'private_key': private_key,
            'owner_id': None,
            'last_seq': 0,
            'created_at': dt.now(timezone.utc),
        }
    else:
        new_room = {
            'name': room.name,
            'description': room.description,
            'type': room.room_type,
            'owner_id': owner_id,
            'last_seq': 0,
            'created_at': dt.now(timezone.utc),
        }

    try:
        room_id = rooms_collection.insert_one(new_room).inserted_id
    except DuplicateKeyError:
        if room.room_type == "private":
            raise HTTPException(
                status_code=409,
                detail="Private chat already exists",
            )
        raise

    all_members = [
        {
            'room_id': room_id,
            'user_id': member_id,
            'role': 
                'owner'
                    if member_id == owner_id else
                'owner'
                    if room.room_type == 'private' else
                'member',
            'last_read_seq': 0,
            'joined_seq': 0,
            'joined_at': dt.now(timezone.utc)
        }
        for member_id in member_ids
    ]

    try: 
        room_members_collection.insert_many(all_members)
    except Exception:
        rooms_collection.delete_one({ "_id": room_id })
        room_members_collection.delete_many({ "room_id": room_id })
        raise

    return {"room_id": str(room_id), "ok": True}


# AUTHORIZED
@router.get("/rooms/{room_id}")
def get_room_details(
    room_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    member = room_members_collection.find_one({ "room_id": rid, "user_id": uid })
    if not member:
        raise HTTPException(status_code=403, detail="User isn't a member of the room")

    room = rooms_collection.find_one({ '_id': rid })
    if not room:
        raise room_not_found_exception

    cursor = room_members_collection.aggregate([
        {
            '$match': {
                'room_id': rid
            }
        },
        {
            '$group': {
                '_id': None, 
                'member_count': {
                    '$sum': 1
                }
            }
        }
    ])

    if room.get('type') == 'private':
        other_member = room_members_collection.find_one({ "room_id": rid, "user_id": { "$ne": uid } }, { "user_id": 1 })

        if other_member:
            other_user = users_collection.find_one({ "_id": other_member['user_id'] }, { 'display_name': 1 })

            if other_user:
                room['other_member'] = other_user['display_name']

    room['_id'] = str(room['_id'])
    room['member_count'] = list(cursor)[0]['member_count']
    room['owner_id'] = str(room['owner_id'])

    return {
        'ok': True,
        'room': room
    }


# AUTHORIZED AND OWNER CHECK
@router.post("/join/room/{room_id}")
def join_room(
    room_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": uid })
    if not user:
        raise user_not_found_exception

    room = rooms_collection.find_one({ "_id": rid }, { 'type': 1 })
    if room.get('type') == 'private':
        raise HTTPException(status_code=403, detail="Cannot join private chat")

    room_member = room_members_collection.find_one({ "room_id": rid, "user_id": uid })
    if room_member:
        return {"message": f"User has already joined the room {room_id}"}

    result = add_person_to_room(uid, rid, role='member')

    return {'member-id': str(result.inserted_id), 'ok': True}


# AUTHORIZED
@router.get("/search/rooms")
def search_rooms(
    search: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        uid = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    clean_search = re.escape(search.strip())

    rooms_cursor = rooms_collection.find({
        "$or": [
            { "name": clean_search },
            { "name": { "$regex": clean_search, "$options": "i" } }
        ]
    })
    
    rooms = {}
    for room in rooms_cursor:
        rooms[room["_id"]] = room

    if not rooms:
        return {"rooms": [], "ok": True}

    room_ids = list(rooms.keys())

    memberships = {
        m["room_id"]: m 
        for m in room_members_collection.find({
            "user_id": uid,
            "room_id": { "$in": room_ids }
        }, { "_id": 0, "room_id": 1, "last_read_seq": 1 })
    }

    pipeline_rooms = list(rooms_collection.aggregate([
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
    ]))

    for room in pipeline_rooms:
        rooms[room["_id"]].update(room)

    private_ids = [rid for rid, r in rooms.items() if r.get("type") == "private"]
    other_user_of = {}
    if private_ids:
        for m in room_members_collection.find(
            { "room_id": { "$in": private_ids }, "user_id": { "$ne": uid } },
            { "_id": 0, "room_id": 1, "user_id": 1 },
        ):
            other_user_of[m["room_id"]] = m["user_id"]

    needed_user_ids = set(other_user_of.values())
    for r in rooms.values():
        lm = r.get("last_message")
        if lm:
            needed_user_ids.add(lm[0]["sender_id"])

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
    for room_id, room in rooms.items():
        if room.get("type") == "private":
            name = names.get(other_user_of.get(room_id))
        else:
            name = room.get("name")

        last_message = None
        if room.get("last_message"):
            lm = room["last_message"][0]
            lm["display_name"] = "you" if lm["sender_id"] == uid else names.get(lm["sender_id"])
            lm["sender_id"] = str(lm["sender_id"])
            last_message = lm

        membership = memberships.get(room_id)
        if membership:
            unread_count = room.get("last_seq", 0) - membership.get("last_read_seq", 0)
            is_member = True
        else:
            unread_count = 0
            is_member = False

        result.append({
            "room_id": str(room_id),
            "type": room.get("type"),
            "name": name,
            "last_message": last_message,
            "unread_count": unread_count,
            "is_member": is_member,
        })

    return {"rooms": result, "ok": True}


# AUTHORIZED AND OWNER CHECK
@router.post("/room/{room_id}/add-people")
def add_people(
    room_id: str,
    adding_users: AddUsersRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
        candidate_uids = [ObjectId(u) for u in adding_users.users]
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": uid })
    if not user:
        raise user_not_found_exception

    room_member = room_members_collection.find_one({ "room_id": rid, "user_id": uid })
    if room_member['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Permission denied")

    result = add_people_to_room(candidate_uids, rid)

    return {
        "ok": True,
        "result": result
    }


# AUTHORIZED AND OWNER CHECK
@router.delete("/room/{room_id}/kick")
def kick_person(
    room_id: str,
    kicking_user_id: str,
    user_id: str = Depends(get_current_user_id),
):

    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
        kicking_uid = ObjectId(kicking_user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    # Validate that User whos kicking isn't member (should be admin or owner)
    user = room_members_collection.find_one({ "room_id": rid, "user_id": uid }, { 'role': 1 })
    if not user:
        raise user_not_found_exception
    if user.get('role', 'member') == 'member':
        raise HTTPException(status_code=403, detail='Access denied')

    # Validate room exists and its not private room
    room = rooms_collection.find_one({ "_id": rid }, { 'type': 1 })
    if not room:
        raise room_not_found_exception
    if room.get('type') == 'private':
        raise HTTPException(status_code=403, detail="Cannot kick person from private chat")

    # Validate that User being kicked isn't the owner of the group
    kicking_user = room_members_collection.find_one({ "room_id": rid, "user_id": kicking_uid }, { 'role': 1, '_id': 1 })
    if not kicking_user:
        raise HTTPException(status_code=404, detail=f"User not found '{str(kicking_uid)}'")
    if kicking_user.get('role', 'member') == 'owner' or kicking_user.get('role', 'member') == 'admin':
        raise HTTPException(status_code=403, detail="Cannot kick owner")

    del_count = room_members_collection.delete_one({ "_id": kicking_user['_id'] }).deleted_count
    return {
        'ok': True,
        'deleted_docs': del_count,
    }


# AUTHORIZED AND OWNER CHECK
@router.delete("/remove-people/{room_id}")
def remove_people(
    room_id: str,
    user_id: str,
    removing_users: RemoveUsersRequest,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    try:
        rid = ObjectId(room_id)
        uid = ObjectId(user_id)
        candidate_uids = [ObjectId(u) for u in removing_users.users]
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": uid })
    if not user:
        raise user_not_found_exception

    room = rooms_collection.find_one({ "_id": rid }, { "type": 1 })
    if not room:
        raise room_not_found_exception
    if room.get('type', '') == 'private':
        raise HTTPException(status_code=403, detail='Cannot remove people from private chat')

    member = room_members_collection.find_one({ "room_id": rid, "user_id": uid }, { 'role': 1 })
    if member.get('role', 'member') != 'owner':
        raise HTTPException(status_code=403, detail="Access denied")

    res = remove_people_from_room(candidate_uids, room, rid)
    return res


# AUTHORIZED
@router.get("/room/{room_id}/members")
def get_room_members(
    room_id: str,
    user_id: str = Depends(get_current_user_id)
):
    if not has_user_joined_the_room(user_id, room_id):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")

    try:
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    cursor = room_members_collection.find({ "room_id": rid })
    room_members = list(cursor)
    user_ids = [doc['user_id'] for doc in room_members]
    cursor = users_collection.find(
        { "_id": { "$in": user_ids } },
        { "display_name": 1, "username": 1 }
    )
    result = list(cursor)
    users_map = {user['_id']: user for user in result}

    for member in room_members:
        member['display_name'] = users_map.get(member['user_id'], {}).get('display_name', 'Deleted user')
        member['username'] = users_map.get(member['user_id'], {}).get('username', 'Deleted user')
        member['_id'] = str(member['_id'])
        member['user_id'] = str(member['user_id'])
        member['room_id'] = str(member['room_id'])

    return {
        'ok': True,
        'member_count': len(room_members),
        'members': room_members
    }


# AUTHORIZED
@router.get("/room/{room_id}/online-members")
def get_onine_people(
    room_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    if not has_user_joined_the_room(current_user_id, room_id):
        raise HTTPException(status_code=403, detail="User hasn't joined the room")

    try:
        room_id = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    active_users = get_online_users(room_id)

    return {"online_users": active_users}


class RoomConnectionManager:
    def __init__(self):      # { room_id: { WebSocket: user_id, ... } }
        self.active_connections: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str, is_subscribing: bool | None = None):
        if not is_subscribing:
            has_user_joined = self.is_user_a_member(user_id, room_id)
            if not has_user_joined:
                return False

        if room_id not in self.active_connections:
            self.active_connections[room_id] = { websocket: user_id }
        else:
            if not websocket in self.active_connections[room_id]:
                self.active_connections[room_id][websocket] = user_id

        return True

    async def broadcast_to_room(self, room_id: str, payload: dict, exclude_ws: WebSocket | None = None):
        dead_cons = []
        sended_cons = []
        for connection in list(self.active_connections.get(room_id, [])):
            if connection == exclude_ws:
                continue

            try:
                await connection.send_json(payload)
                sended_cons.append(connection)
            except Exception:
                dead_cons.append(connection)

        for connection in dead_cons:
            await self.disconnect(connection, room_id)

    async def subscribe(self, websocket: WebSocket, user_id: str, room_id: str):
        return await self.connect(websocket, user_id, room_id, True)

    async def disconnect(self, websocket: WebSocket, room_id: str | None = None):
        if not room_id:
            for rid, value in self.active_connections.items():
                for ws in value:
                    if ws == websocket:
                        try:
                            self.active_connections[rid].pop(websocket)
                            return
                        except:
                            return

        connections = self.active_connections.get(room_id, [])
        if not connections:
            return

        if websocket in connections:
            connections.pop(websocket)

        if not connections:
            self.active_connections.pop(room_id, None)

    def is_user_a_member(self, user_id: str, room_id: str):
        try:
            uid = ObjectId(user_id)
            rid = ObjectId(room_id)
        except bson.errors.InvalidId:
            return False

        room = rooms_collection.find_one({ "_id": rid })
        user = users_collection.find_one({ "_id": uid })
        if not room or not user:
            return False

        member = room_members_collection.find_one({ 'room_id': rid, 'user_id': uid })
        if not member:
            print(f"{str(rid)}, {str(uid)}")
            print("Not a member")
            return False

        return True


manager = RoomConnectionManager()

@router.websocket("/ws")
async def websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    user_id = user_id_from_token(token) if token else None

    try:
        uid = ObjectId(user_id)
        user_rooms = list(room_members_collection.find({ "user_id": uid }, { "_id": 0, "room_id": 1 }))
        rids = []

        if user_rooms:
            rids = [ObjectId(u['room_id']) for u in user_rooms]
    except bson.errors.InvalidId:
        await websocket.close(code=1008, reason='invalid id')
        return

    for rid in set(rids):
        is_allowed = await manager.connect(websocket, user_id, str(rid))
        if not is_allowed:
            await websocket.close(code=1008)
            return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get('type', '')
            room_id = data.get('room_id')
            rid = ObjectId(room_id)

            if event_type == 'subscribe':
                is_allowed = await manager.subscribe(websocket, user_id, room_id)
                if not is_allowed:
                    await websocket.send_json({
                        "type": "error",
                        "error": "user_not_in_room"
                    })
                    continue

                await websocket.send_json({
                    'type': 'subscribed',
                    'room_id': room_id
                })
            elif event_type == 'typing':
                if not user_id:
                    await websocket.send_json({
                        "type": 'error',
                        'error': 'user_id_missing'
                    })
                    continue

                if not manager.is_user_a_member(user_id, room_id):
                    await websocket.send_json({
                        "type": "error",
                        "error": "user_not_in_room"
                    })
                    continue

                is_typing = data.get('is_typing')

                sender = users_collection.find_one(
                    { "_id": uid }, { "username": 1, "display_name": 1 }
                )

                typing_payload = {
                    "type": "typing",
                    "room_id": room_id,
                    "user_id": user_id,
                    "is_typing": is_typing,
                    "user": {
                        "id": user_id,
                        "username": sender.get("username") if sender else None,
                        "display_name": sender.get("display_name") if sender else "User",
                    }
                }

                # Broadcast to all room members except the sender
                await manager.broadcast_to_room(room_id, typing_payload, exclude_ws=websocket)
            elif event_type == 'message_edited':
                pass
            else:
                if not has_user_joined_the_room(user_id, room_id):
                    await websocket.send_json({"type": "error", "error": "user_not_in_room"})
                    continue

                # Get the last-seq and update it
                room = rooms_collection.find_one_and_update(
                    { "_id": ObjectId(room_id) },
                    { "$inc": { "last_seq": 1 } },
                    return_document=ReturnDocument.AFTER
                )

                if room is None:
                    await websocket.send_json({"type": "error", "error": "room_not_found"})
                    continue
            
                # Save it do the database
                now = dt.now(timezone.utc)
                seq = room['last_seq']
                doc = {
                    "room_id": rid,
                    "sender_id": uid,
                    "seq": seq,
                    "body": data['body'],
                    "created_at": now,
                    "edited_at": None,
                    "deleted": False,
                }
                result = messages_collection.insert_one(doc)

                # Payload sended to all connections
                sender = users_collection.find_one(
                    { "_id": uid }, { "username": 1, "display_name": 1 }
                )

                payload = {
                    "type": "new_message",
                    "id": str(result.inserted_id),
                    "room_id": room_id,
                    "seq": seq,
                    "body": data['body'],
                    "created_at": now.isoformat(),
                    "edited_at": None,
                    "deleted": False,
                    "sender": {
                        "id": str(uid),
                        "username": sender.get("username") if sender else None,
                        "display_name": sender.get("display_name") if sender else "Deleted user",
                    },
                }

                await manager.broadcast_to_room(room_id, payload)

    except WebSocketDisconnect:
        pass
    except bson.errors.InvalidId:
        pass
    finally:
        await manager.disconnect(websocket)
