import asyncio

from datetime import datetime

from sqlalchemy import DateTime
from app.api import reservation
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.user import User
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreateRequest, ReservationResponse
from sqlalchemy.orm import Session
from app.common.exception import BusinessException


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    """创建预约记录"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    if data.date < current_date:
        raise BusinessException(message="预约日期不能早于当前日期")
    if current_date == data.date and data.start_time <= current_time:
        raise BusinessException(message="预约开始时间不能早于当前时间")
    if data.start_time >= data.end_time:
        raise BusinessException(message="预约结束时间不能早于开始时间")
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")
    if data.start_time < lab.open_time:
        raise BusinessException(message="预约开始时间不能早于实验室开放时间")
    if data.end_time > lab.close_time:
        raise BusinessException(message="预约结束时间不能晚于实验室关闭时间")
    if data.equipment_id:
        equipment = (
            db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        )
        if not equipment:
            raise BusinessException(message="设备不存在")
        if equipment.lab_id != data.lab_id:
            raise BusinessException(message="该设备不属于所属实验室")
        if equipment.status != 1:
            raise BusinessException(message="设备维修中")
    # 先找同一实验室、同一天的预约，再只保留状态为 0 待审核或 1 已通过的记录，检查时间是否重叠。如果是预约设备再限定设备
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )
    if data.equipment_id:
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:
        query = query.filter(Reservation.equipment_id.is_(None))
    res = query.first()
    if res:
        raise BusinessException(message="该时段已被预约")
    reservation_model = Reservation(
        user_id=current_user.id,
        date=data.date,
        lab_id=data.lab_id,
        start_time=data.start_time,
        end_time=data.end_time,
        equipment_id=data.equipment_id,
        remark=data.remark,
    )
    db.add(reservation_model)
    db.commit()


def get_page_reservation_list(
    db: Session,
    page: int,
    page_size: int,
    current_user: User,
    status: int | None = None,
):
    """查询预约记录"""
    query = db.query(Reservation)
    if current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id is not None else "实验室"
        result.append(res)
    return PageResponse(list=result, total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """学生取消预约"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="无权限", code=403)
    if item.status != 0:
        raise BusinessException(message="无法取消预约")
    item.status = 3
    db.commit()


def audit_reservation(db: Session, status: int, reservation_id: int):
    if status not in [1, 2]:
        raise BusinessException(message="审核状态错误")
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status != 0:
        raise BusinessException(message="当前状态不支持审核")
    item.status = status
    db.commit()


def expire_pending_reservation():
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M")
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        change = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= now_time):
                item.status = 3
                change = True
        if change:
            db.commit()

    finally:
        db.close()


async def run_expire_scan():
    while True:
        expire_pending_reservation()
        await asyncio.sleep(60)
