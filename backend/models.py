from pydantic import BaseModel, Field

class UsersRequest(BaseModel):
    name: str
    username: str
    email: str = "user@example.com"
    password: str = Field(..., min_length=5, max_length=72)
    bio: str | None = None


class RoomRequest(BaseModel):
    name: str
    description: str | None = None
    members: list[str]