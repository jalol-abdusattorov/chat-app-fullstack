from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

swagger_bearer_scheme = HTTPBearer(auto_error=False)

def check_owner(request: Request, user_id):
    if request.state.user.get('uid') != user_id:
        raise HTTPException(status_code=403, detail="Permission denied, not the owner")
