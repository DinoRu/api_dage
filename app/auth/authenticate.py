from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.auth.jwt_handler import verify_access_token
from app.db.session import get_db
from app.schema.user import TokenData
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/signin")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign in to access"
        )
    data = verify_access_token(token)
    payload = data.get("user", {})
    user_id: str = payload.get("user_id")
    username: str = payload.get("username")
    department: str = payload.get("department")
    if user_id is None or username is None or department is None:
        raise credential_exception
    token_data = TokenData(user_id=user_id, username=username, department=department)
    service = UserService(db)
    user = await service.get_user(token_data.user_id)  # Assurez-vous que `get_user` est une méthode asynchrone dans UserService
    if user is None:
        raise credential_exception
    return user