from pydantic import BaseModel, Field

class UsersRequest(BaseModel):
    username: str
    display_name: str
    email: str = "user@example.com"
    password: str = Field(..., min_length=5, max_length=72)
    bio: str | None = None

class RoomRequest(BaseModel):
    name: str | None = None
    room_type: str
    room_members: list[str]
    description: str | None = None

class AddUsersRequest(BaseModel):
    users: list[str]

class RemoveUsersRequest(BaseModel):
    users: list[str]