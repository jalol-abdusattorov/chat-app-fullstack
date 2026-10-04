import bson
from bson import ObjectId
from datetime import datetime as dt, timezone
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect

from models import AddUsersRequest, RemoveUsersRequest, RoomRequest
from db import users_collection, privates_collection, groups_collection, messages_collection

invalid_id_exception = HTTPException(status_code=403, detail="invalid id")
router = APIRouter()

@router.post("/create/room/private/{user_id}")
def create_private_room(
    user_id: str,
    room: RoomRequest
):
    if len(room.members) != 2:
        raise HTTPException(status_code=403, detail="Only 2 members")

    try:
        user_id = ObjectId(user_id)

        first_member = ObjectId(room.members[0])
        second_member = ObjectId(room.members[1])

        first_user = users_collection.find_one({ "_id": first_member })
        second_user = users_collection.find_one({ "_id": second_member })

        if first_member != user_id and second_member != user_id:
            raise HTTPException(status_code=403, detail="Cannot create private room for other people")
        if first_member == second_member:
            raise HTTPException(status_code=403, detail="Both ids are the same")
        if not first_user or not second_user:
            raise HTTPException(status_code=404, detail="Cannot find the user(s)")


        new_room = {
            "name": room.name,
            "description": room.description,
            "members": [
                first_member,
                second_member
            ],
            "created_at": dt.now(timezone.utc)
        }

        room_id = privates_collection.insert_one(new_room).inserted_id

        # adding the room_id to the both users joined_rooms
        users_collection.update_one({ "_id": first_member }, { "$push": { "joined_rooms": room_id } })
        users_collection.update_one({ "_id": second_member }, { "$push": { "joined_rooms": room_id } })

        return {'room_id': str(room_id)}
    except bson.errors.InvalidId:
        raise invalid_id_exception


@router.post("/create/room/group/{user_id}")
def create_group_room(
    user_id: str,
    room: RoomRequest
):
    try:
        user_id = ObjectId(user_id)

        all_members = []
        for member_id in room.members:
            member_id = ObjectId(member_id)
            user_exists = users_collection.find_one({ "_id": member_id })

            if not user_exists:
                raise HTTPException(status_code=403, detail=f"Invalid id '{str(member_id)}'")

            all_members.append(member_id)

        new_room = {
            "name": room.name,
            "description": room.description,
            "members": all_members,
            "owner": user_id,
            "created_at": dt.now(timezone.utc)
        }

        room_id = groups_collection.insert_one(new_room).inserted_id
        for member in all_members:
            users_collection.update_one({ "_id": member }, { "$push": { "joined_rooms": room_id } })

        return {'room_id': str(room_id)}
    except bson.errors.InvalidId:
        raise invalid_id_exception


@router.post("/join/room/{room_id}")
def join_room(
    room_id: str,
    user_id: str
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    user = users_collection.find_one({ "_id": user_id })
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    room = privates_collection.find_one({ "_id": room_id })
    room_type = "private"
    if not room:
        room = groups_collection.find_one({ "_id": room_id })
        room_type = "group"
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room_members = [room_member for room_member in room['members']]
    if user_id in room_members:
        raise HTTPException(status_code=403, detail="User has already joined")

    users_collection.update_one({ "_id": user_id }, { "$push": { "joined_rooms": room_id } })
    if room_type == "private":
        privates_collection.update_one({ "_id": room_id }, { "$push": { "members": user_id } })
    else:
        groups_collection.update_one({ "_id": room_id }, { "$push": { "members": user_id } })

    return {'message': 'Joined successfuly'}


@router.post("/add-people/{room_id}")
def add_people(
    room_id: str,
    user_id: str,
    users: AddUsersRequest
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)

        user = users_collection.find_one({ "_id": user_id })
        if not user:
            raise HTTPException(status_code=404, detail=f"Adder not found '{str(user_id)}'")

        room = privates_collection.find_one({ "_id": room_id })
        if room:
            raise HTTPException(status_code=403, detail="Cannot invite people to private chat")

        room = groups_collection.find_one({ "_id": room_id })
        room_members = [room_member for room_member in room['members']]

        if user_id not in room_members:
            raise HTTPException(status_code=403, detail="User hasn't joined the chat")

        added_user_ids = []
        added_count = 0
        tried_count = 0
        for i in users.users:
            i = ObjectId(i)

            temp = users_collection.find_one({ "_id": i })
            if not temp:
                raise HTTPException(status_code=404, detail=f"User not found '{str(i)}'")

            if not i in room_members:
                users_collection.update_one({ "_id": i }, { "$push": { "joined_rooms": room_id } })
                groups_collection.update_one({ "_id": room_id }, { "$push": { "members": i } })

                added_user_ids.append(str(i))

                added_count += 1
            else:
                tried_count += 1

        return {
            'added_count': added_count,
            'tried_count': tried_count,
            'added_users': added_user_ids
        }

    except bson.errors.InvalidId:
        raise invalid_id_exception


@router.delete("/remove-people/{room_id}")
def remove_people(
    room_id: str,
    user_id: str,
    users: RemoveUsersRequest,
):
    try:
        room_id = ObjectId(room_id)
        user_id = ObjectId(user_id)

        room = privates_collection.find_one({ "_id": room_id })
        if room:
            raise HTTPException(status_code=403, detail="Cannot remove people from private chat")

        room = groups_collection.find_one({ "_id": room_id })
        if not room:
            raise HTTPException(status_code=403, detail="room not found")

        room_members = [room_member for room_member in room['members']]
        if room.get('owner') != user_id:
            print(room)
            print(room.get('owner'))
            print(user_id)
            raise HTTPException(status_code=403, detail="Permission denied, not the owner of group")

        user = users_collection.find_one({ "_id": user_id })
        if not user:
            raise HTTPException(status_code=403, detail=f"Remover not found '{user}")
        if user_id not in room_members:
            raise HTTPException(status_code=403, detail="User hasn't joined the room")

        removed_user_ids = []
        removed_count = 0
        for i in users.users:
            i = ObjectId(i)
            adding_user = users_collection.find_one({ "_id": i })
            if not adding_user:
                raise HTTPException(status_code=404, detail=f"User not found '{str(i)}")

            if i not in room_members:
                raise HTTPException(status_code=403, detail=f"User not in room '{str(i)}'")

            if i == room['owner']:
                raise HTTPException(status_code=403, detail="Cannot remove owner")

            groups_collection.update_one({ "_id": room_id }, { "$pull": { "members": i } })
            users_collection.update_one({ "_id": i }, { "$pull": { "joined_rooms": room_id } })
            removed_user_ids.append(str(i))
            removed_count += 1

        return {
            'removed_count': removed_count,
            'removed_users': removed_user_ids
        }

    except bson.errors.InvalidId:
        raise invalid_id_exception


@router.get("/room/{room_id}/members")
def get_room_members(
    room_id: str,
):
    try:
        room_id = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room = privates_collection.find_one({ "_id": room_id })
    if not room:
        room = groups_collection.find_one({ "_id": room_id })

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

    return {'members': room['members']}


@router.get("/room/{room_id}/online-members")
def get_onine_people(
    room_id: str
):
    try:
        room_id = ObjectId(room_id)
    except bson.errors.InvalidId:
        raise invalid_id_exception

    room = privates_collection.find_one({ "_id": room_id })
    if not room:
        room = groups_collection.find_one({ "_id": room_id })

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

    active_users = []
    connections = manager.active_connections.get(str(room_id))
    if connections:
        active_users = list(connections.values())

    print(active_users)

    return {"online_users": active_users}

class ConnectionManager:
    def __init__(self):      # { room_id: { WebSocket: user_id, ... } }
        self.active_connections: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str):
        room = self.get_room(room_id)
        is_users_room = self.users_room(user_id, room, room_id)

        if not room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False
        if not is_users_room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = { websocket: user_id }
        else:
            self.active_connections[room_id][websocket] = user_id

        return True

    async def broadcast_to_room(self, message: dict):
        room_id = message['room_id']
        connections = self.active_connections.get(room_id, [])

        for connection in connections:
            await connection.send_json(message)

    async def disconnect(self, websocket, room_id):
        self.active_connections[room_id].pop(websocket)

    def get_room(self, room_id):
        try:
            room = privates_collection.find_one({ "_id": ObjectId(room_id) })
            if not room:
                room = groups_collection.find_one({ "_id": ObjectId(room_id) })
                if not room:
                    return False

                return room

            return room
        except bson.errors.InvalidId:
            return False

    def users_room(self, user_id, room, room_id):
        try:
            user = users_collection.find_one({ "_id": ObjectId(user_id) })
            if not user:
                return False

            if ObjectId(room_id) not in [i for i in user['joined_rooms']]:
                return False
            if ObjectId(user_id) not in [i for i in room['members']]:
                return False

            return True
        except bson.errors.InvalidId:
            return False

manager = ConnectionManager()

@router.websocket("/ws/{user_id}/{room_id}")
async def websocket(
    user_id: str,
    room_id: str,
    websocket: WebSocket,
):
    is_allowed = await manager.connect(websocket, user_id, room_id)

    if not is_allowed:
        return

    try:
        while True:
            data = await websocket.receive_text()

            message = {
                "room_id": ObjectId(room_id),
                "sender_id": ObjectId(user_id),
                "data": data,
                "created_at": dt.now(timezone.utc).isoformat()
            }

            result = messages_collection.insert_one(message)

            message['_id'] = str(result.inserted_id)
            message['room_id'] = str(message['room_id'])
            message['sender_id'] = str(message['sender_id'])

            await manager.broadcast_to_room(message)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
    except bson.errors.InvalidId:
        await manager.disconnect(websocket, room_id)
