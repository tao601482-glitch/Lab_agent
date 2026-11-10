from app.api.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.common.response import Response
from app.schemas.lab import LabCreateRequest, LabUpdateRequest
from app.services import lab_service
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.database import get_db

router = APIRouter(prefix="/lab", tags=["实验室管理"])


@router.get("/list")
def get_lab_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = lab_service.get_lab_page_list(
        db=db, page=page, page_size=page_size, keywords=keywords, status=status
    )
    return Response.success(data=res)


@router.get("/{lab_id}")
def get_lab(
    lab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = lab_service.get_lab(lab_id=lab_id, db=db)
    return Response.success(data=res)


@router.post("")
def create_lab(
    data: LabCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    res = lab_service.create_lab(db=db, data=data)
    return Response.success(data=res)


@router.put("/{lab_id}")
def update_lab(
    data: LabUpdateRequest,
    lab_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.update_lab(db=db, lab_id=lab_id, data=data)
    return Response.success(data=res)


@router.delete("/{lab_id}")
def delete_lab(
    lab_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lab_service.delete_lab(db=db, lab_id=lab_id)
    return Response.success(message="删除成功")
