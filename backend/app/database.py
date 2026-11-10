from sqlalchemy.orm import sessionmaker,DeclarativeBase,Mapped,mapped_column
from sqlalchemy import create_engine,DateTime
from app.config import settings
from datetime import datetime

# 根据配置里的数据库地址，创建一个数据库引擎。
engine = create_engine(settings.DATABASE_URL)

# 数据库session会话的连接工厂
SessionLocal = sessionmaker(bind=engine,autoflush=False)

# 创建会话 → 交给接口使用 → 使用结束后关闭会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    id:Mapped[int] = mapped_column(
        primary_key=True,autoincrement=True,comment="主键ID",sort_order=-1
    )
    create_time:Mapped[datetime] = mapped_column(
        DateTime,default=datetime.now,comment="创建时间",sort_order=1
    )
    update_time:Mapped[datetime] = mapped_column(
        DateTime,default=datetime.now,onupdate=datetime.now,comment="更新时间",sort_order=2
    )
