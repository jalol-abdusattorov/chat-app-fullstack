from typing import Annotated
import bson
from bson import ObjectId
from datetime import datetime as dt, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from pymongo import ReturnDocument

from models import AddUsersRequest, RemoveUsersRequest, RoomRequest
from db import users_collection, rooms_collection, messages_collection, room_members_collection
from routes.route_utils import swagger_bearer_scheme, check_owner

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
    for room in manager.active_connections:
        for _id in room.values():
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
@router.post("/rooms/create-room/{user_id}")
def create_room(
    user_id: str,
    room: RoomRequest,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

    try:
        user_id = ObjectId(user_id)
        user = users_collection.find_one({ "_id": user_id })
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found '{str(user_id)}'")
        if room.room_type == 'private' and len(room.room_members) != 2:
            raise HTTPException(status_code=403, detail="Cannot add more/less than 2 members")
        if len(set(room.room_members)) != len(room.room_members):
            raise HTTPException(status_code=403, detail="Cannot have duplicate users")

        if room.room_type == "private":
            new_room = {
                'name': None,
                'description': room.description,
                'type': room.room_type,
                'owner_id': None,
                'last_seq': 0,
                'created_at': dt.now(timezone.utc)
            }

        elif room.room_type == "group":
            new_room = {
                'name': room.name,
                'description': room.description,
                'type': room.room_type,
                'owner_id': user_id,
                'last_seq': 0,
                'created_at': dt.now(timezone.utc)
            }
        else:
            raise HTTPException(status_code=403, detail="Invalid room type")

        room_id = rooms_collection.insert_one(new_room).inserted_id

        all_members = []
        for member_id in room.room_members:
            member_id = ObjectId(member_id)
            member = users_collection.find_one({ "_id": member_id })
            if not member:
                rooms_collection.delete_one({ "_id": room_id })
                raise HTTPException(status_code=404, detail=f"User not found '{str(member_id)}'")

            new_member = {
                'room_id': room_id,
                'user_id': member_id,
                'role': 'owner' if member_id == user_id else 'owner' if room.room_type == 'private' else 'member',
                'last_read_seq': 0,
                'joined_seq': 0,
                'joined_at': dt.now(timezone.utc)
            }
            all_members.append(new_member)


        room_members_collection.insert_many(all_members)

        return {"room_id": str(room_id)}

    except bson.errors.InvalidId:
        raise invalid_id_exception


# AUTHORIZED AND OWNER CHECK
@router.post("/join/room/{room_id}")
def join_room(
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

    return {'member-id': str(result.inserted_id), 'state': 'success'}


# AUTHORIZED AND OWNER CHECK
@router.post("/room/{room_id}/add-people")
def add_people(
    room_id: str,
    user_id: str,
    adding_users: AddUsersRequest,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

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
        raise

    result = add_people_to_room(candidate_uids, rid)

    return result


# AUTHORIZED AND OWNER CHECK
@router.delete("/room/{room_id}/kick")
def kick_person(
    room_id: str,
    user_id: str,
    kicking_user_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    check_owner(request, user_id)

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
        'status': 'success',
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

    # try:
    #     room_id = ObjectId(room_id)
    #     user_id = ObjectId(user_id)

    #     room = privates_collection.find_one({ "_id": room_id })
    #     if room:
    #         raise HTTPException(status_code=403, detail="Cannot remove people from private chat")

    #     room = groups_collection.find_one({ "_id": room_id })
    #     if not room:
    #         raise HTTPException(status_code=403, detail="room not found")

    #     room_members = [room_member for room_member in room['members']]
    #     if room.get('owner') != user_id:
    #         raise HTTPException(status_code=403, detail="Permission denied, not the owner of group")

    #     user = users_collection.find_one({ "_id": user_id })
    #     if not user:
    #         raise HTTPException(status_code=403, detail=f"Remover not found '{user}")
    #     if user_id not in room_members:
    #         raise HTTPException(status_code=403, detail="User hasn't joined the room")

    #     removed_user_ids = []
    #     removed_count = 0
    #     for i in users.users:
    #         i = ObjectId(i)
    #         adding_user = users_collection.find_one({ "_id": i })
    #         if not adding_user:
    #             raise HTTPException(status_code=404, detail=f"User not found '{str(i)}")

    #         if i not in room_members:
    #             raise HTTPException(status_code=403, detail=f"User not in room '{str(i)}'")

    #         if i == room['owner']:
    #             raise HTTPException(status_code=403, detail="Cannot remove owner")

    #         groups_collection.update_one({ "_id": room_id }, { "$pull": { "members": i } })
    #         users_collection.update_one({ "_id": i }, { "$pull": { "joined_rooms": room_id } })
    #         removed_user_ids.append(str(i))
    #         removed_count += 1

    #     return {
    #         'removed_count': removed_count,
    #         'removed_users': removed_user_ids
    #     }

    # except bson.errors.InvalidId:
    #     raise invalid_id_exception


# AUTHORIZED
@router.get("/room/{room_id}/members")
def get_room_members(
    room_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    try:
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    cursor = room_members_collection.find({ "room_id": rid })
    room_members = list(cursor)

    for room_member in room_members:
        room_member['_id'] = str(room_member['_id'])
        room_member['room_id'] = str(room_member['room_id'])
        room_member['user_id'] = str(room_member['user_id'])

    return {
        'member_count': len(room_members),
        'members': room_members
    }


# AUTHORIZED
@router.get("/room/{room_id}/online-members")
def get_onine_people(
    room_id: str,
    request: Request,
    _: Annotated[str, Depends(swagger_bearer_scheme)]
):
    try:
        room_id = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room = rooms_collection.find_one({ "_id": room_id })
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    active_users = get_online_users(room_id)

    return {"online_users": active_users}


class ConnectionManager:
    def __init__(self):      # { room_id: { WebSocket: user_id, ... } }
        self.active_connections: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str):
        has_user_joined = self.is_user_a_member(user_id, room_id)
        if not has_user_joined:
            print("User hasn't joined the room yet")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = { websocket: user_id }
        else:
            self.active_connections[room_id][websocket] = user_id

        return True

    async def broadcast_to_room(self, room_id: str, payload: dict):
        dead_cons = []
        for connection in list(self.active_connections.get(room_id, [])):
            try:
                await connection.send_json(payload)
            except Exception:
                dead_cons.append(self.connect)

        for connection in dead_cons:
            await self.disconnect(connection, room_id)

    async def disconnect(self, websocket, room_id):
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
            print("Invalid ID")
            return False

        room = rooms_collection.find_one({ "_id": rid })
        user = users_collection.find_one({ "_id": uid })
        if not room or not user:
            print(f'room_id: {str(rid)}')
            print(f'user_id: {str(uid)}')
            print("User or Room not found")
            return False

        member = room_members_collection.find_one({ 'room_id': rid, 'user_id': uid })
        if not member:
            print(f"{str(rid)}, {str(uid)}")
            print("Not a member")
            return False

        return True


manager = ConnectionManager()

@router.websocket("/ws/{user_id}/{room_id}")
async def websocket(
    user_id: str,
    room_id: str,
    websocket: WebSocket,
):
    try:
        uid = ObjectId(user_id)
        rid = ObjectId(room_id)
    except bson.errors.InvalidId:
        await websocket.close(code=1008)
        return

    is_allowed = await manager.connect(websocket, user_id, room_id)
    if not is_allowed:
        return

    try:
        while True:
            text = await websocket.receive_text()

            if not is_user_in_room(user_id, room_id):
                await websocket.send_json({"type": "error", "error": "user_not_in_room"})
                continue

            # Get the last-seq and update it
            room = rooms_collection.find_one_and_update(
                { "_id": rid },
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
                "body": text,
                "created_at": now,
                "edited_at": None,
                "deleted": False,
            }
            result = messages_collection.insert_one(doc)

            # Payload sended to all connections
            payload = {
                "type": "new_message",
                "_id": str(result.inserted_id),
                "room_id": room_id,
                "sender_id": user_id,
                "seq": seq,
                "body": text,
                "created_at": now.isoformat(),
            }

            await manager.broadcast_to_room(room_id, payload)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, room_id)
