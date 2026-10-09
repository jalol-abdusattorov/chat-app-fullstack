import os
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

CONNECTION_STRING = os.getenv("CONNECTION_STRING")
client = MongoClient(CONNECTION_STRING)

db = client.chatsDB
users_collection = db.users
rooms_collection = db.rooms
room_members_collection = db.room_members
messages_collection = db.messages