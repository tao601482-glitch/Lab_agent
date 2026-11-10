from datetime import datetime, timedelta

import jwt
from app.config import settings


def create_access_token(user_id: int) -> str:
    """创建JWT token"""
    expire = datetime.now() + timedelta(
        hours=int(settings.JWT_EXPIRE_HOURS)
    )  # 过期时间
    payload = {"user_id": user_id, "exp": expire}  # JWT记录的数据
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    """解析JWTtoken"""
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
