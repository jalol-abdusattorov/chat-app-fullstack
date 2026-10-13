import bcrypt
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.chatsDB

now = datetime.now(timezone.utc)
test_pw = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()

user_ids = []
for i in range(1, 51):
    uid = ObjectId()
    user_ids.append(uid)
    db.users.insert_one({
        "_id": uid,
        "username": f"testuser{i}",
        "display_name": f"Test {i}",
        "email": f"testuser{i}@example.com",
        "bio": "",
        "password_hash": test_pw,
        "created_at": now,
    })

room_id = ObjectId()
db.rooms.insert_one({
    "_id": room_id, "type": "group", "name": "Load test",
    "owner_id": user_ids[0], "last_seq": 0, "created_at": now,
})

db.room_members.insert_many([{
    "room_id": room_id, "user_id": uid, "role": "member",
    "last_read_seq": 0, "joined_seq": 0, "joined_at": now,
} for uid in user_ids])

print("Room ID:", room_id)