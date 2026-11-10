from fastapi import APIRouter, FastAPI, Depends
from app.common.response import Response
from app.api.dependencies.auth import get_current_admin, get_current_user
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.equipment import EquipmentCreateRequest, EquipmentUpdateRequest
from app.services import equipment_service

router = APIRouter(
    prefix="/equipment", tags=["实验室设备信息接口"]
)  # 创建一个路由对象，可以统一设置一组接口的路径前缀


@router.get("/list")
def get_equipment_list(
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10,
    lab_id: int | None = None,
    current_user: User = Depends(get_current_user),
    keywords: str | None = None,
):
    res = equipment_service.get_equipment_page_list(
        db=db, page=page, page_size=page_size, lab_id=lab_id, keywords=keywords
    )
    return Response.success(data=res)


@router.post("")
def create_equipment(
    data: EquipmentCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.create_equipment(db=db, data=data)
    return Response.success(data=res)


@router.put("/{equipment_id}")
def update_equipment(
    data: EquipmentUpdateRequest,
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    res = equipment_service.update_equipment(
        db=db, data=data, equipment_id=equipment_id
    )
    return Response.success(data=res)


@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    equipment_service.delete_equipment(db=db, equipment_id=equipment_id)
    return Response.success(message="删除成功")
