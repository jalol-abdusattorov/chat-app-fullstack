import os
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

CONNECTION_STRING = os.getenv("CONNECTION_STRING")
client = MongoClient(CONNECTION_STRING)

db = client.chatsDB
users_collection = db.users
privates_collection = db.privates
groups_collection = db.groups
messages_collection = db.messages