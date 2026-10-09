# from datetime import datetime as dt, timezone
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

# from db import rooms_collection, messages_collection


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

