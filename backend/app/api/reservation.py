from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies.auth import get_current_admin, get_current_user
from app.common.response import Response
from app.models.user import User
from app.database import get_db
from app.schemas.reservation import ReservationCreateRequest
from app.services import reservation_service
from app.schemas.reservation import AuditReservationRequest

router = APIRouter(prefix="/reservation", tags=["预约相关接口"])


@router.post("")
def create_reservation(
    data: ReservationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_service.create_reservation(db=db, data=data, current_user=current_user)
    return Response.success(message="预约成功")


@router.get("/list")
def get_page_reservation_list(
    status: int | None = None,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
):
    res = reservation_service.get_page_reservation_list(
        db=db, page=page, page_size=page_size, current_user=current_user, status=status
    )
    return Response.success(data=res)


@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_service.cancel_reservation(
        db=db, current_user=current_user, reservation_id=reservation_id
    )
    return Response.success()


@router.put("/{reservation_id}/audit")
def audit_reservation(
    data: AuditReservationRequest,
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    reservation_service.audit_reservation(
        db=db,
        reservation_id=reservation_id,
        status=data.status,
    )
    return Response.success()
