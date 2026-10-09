Changes:
1. Merge groups and privates into one rooms collection.
rooms collection:
{
  "_id": ObjectId(...),
  "type": "group",          # or "private" / "dm"
  "name": "string",
  "description": "string",
  "owner_id": ObjectId(...),
  "last_seq": 0,
  "created_at": datetime(...)
}


2.Store membership in one place.
room_members collection:
{
  "_id": {"room_id": ObjectId(...), "user_id": ObjectId(...)},
  "role": "owner",          # "owner" | "admin" | "member"
  "last_read_seq": 0,
  "joined_seq": 0,
  "joined_at": datetime(...)
}


3. Add seq to messages.
messages collection:
{
  "_id": ObjectId(...),
  "room_id": ObjectId(...),
  "sender_id": ObjectId(...),
  "seq": 42,
  "body": "this message is edited",   # rename from "data"
  "created_at": datetime(...),         # a real datetime, not a string
  "edited_at": datetime(...),          # instead of a bare boolean
  "deleted": False
}


4. Make created_at a real date.
5. Use soft deletes for messages. A deleted: True flag with the body cleared keeps seq gaps harmless and avoids the hard-delete issue from earlier.
