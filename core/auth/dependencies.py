from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.auth.security import verify_token
from core.auth.models import User
# from core.database import get_session # Mocked for now

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    # In a real app, fetch user from DB to check if active
    return User(username=username, hashed_password="dummy")

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# RBAC Dependency
def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        # Mock role checking: In reality, join with role table and verify permissions
        if current_user.role and current_user.role.name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role: {required_role}"
            )
        return current_user
    return role_checker
