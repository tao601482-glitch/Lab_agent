import bcrypt


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password) -> bool:
    """验证密码有效性"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
