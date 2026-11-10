from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.utils.jwt import decode_access_token
from app.database import get_db
from sqlalchemy.orm import Session
from app.common.exception import BusinessException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """JWT token 鉴权验证合法性"""
    try:
        # 验证并解析token
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录"
        )
    # 取出user_id
    user_id = payload.get("user_id")
    # 检查user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证"
        )
    # 查询用户信息
    user = db.query(User).filter(User.id == user_id).first()
    # 检查用户是否存在
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或登录凭证失效"
        )
    # 检查用户状态
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户被禁用")
    return user


def get_current_admin(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为管理员"""
    if current_user.role != "admin":
        raise BusinessException(message="无权限访问", code=403)
    return current_user
