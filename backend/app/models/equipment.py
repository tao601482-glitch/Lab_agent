from app.database import Base
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.lab import Lab


class Equipment(Base):
    __tablename__ = "equipments"
    __table_args__ = {"comment": "实验室设备管理表"}
    lab_id: Mapped[int] = mapped_column(
        ForeignKey("labs.id"), comment="所属实验室", nullable=False
    )  # 设备表中的 lab_id，对应实验室表中的 id
    name: Mapped[str] = mapped_column(String(50), comment="设备名称", nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(500), comment="说明", nullable=True
    )
    img: Mapped[str | None] = mapped_column(String(200), comment="图片", nullable=True)
    spec: Mapped[str | None] = mapped_column(
        String(100), comment="规格型号", nullable=True
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        comment="数量",
        default=1,
    )
    status: Mapped[int] = mapped_column(
        Integer, comment="状态:0-维修,1-正常", default=1
    )
    lab: Mapped[Lab] = relationship()  # 直接获取对应的实验室对象。
