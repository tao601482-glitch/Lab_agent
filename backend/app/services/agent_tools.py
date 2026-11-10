from datetime import datetime
from langchain_core.tools import tool
import json
from sqlalchemy.orm import Session
from app.common.exception import BusinessException
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest
from app.services import equipment_service, kb_service, lab_service, reservation_service


def build_tools(db: Session, current_user: User):
    @tool
    def search_lab_docs(query: str) -> str:
        """根据用户提问检索知识库"""
        try:
            return kb_service.search(query=query) or "没有检索到相关资料"
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_open_labs(keywords: str = "") -> str:
        """查询开放的实验室列表"""
        try:
            keywords = keywords.strip() or None
            page = lab_service.get_lab_page_list(
                db=db, page=1, page_size=10, keywords=keywords, status=1
            )
            rows = []
            for item in page.list:
                lab = {
                    "id": item.id,
                    "name": item.name,
                    "location": item.location,
                    "capacity": item.capacity,
                    "open_time": item.open_time,
                    "close_time": item.close_time,
                }
                rows.append(lab)
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_lab_equipments(lab_id: int, keywords: str = "") -> str:
        """查询某个实验室的设备"""
        try:
            keywords = keywords.strip() or None
            page = equipment_service.get_equipment_page_list(
                db=db, page=1, page_size=10, lab_id=lab_id, keywords=keywords
            )
            rows = []
            for item in page.list:
                equipment = {
                    "id": item.id,
                    "name": item.name,
                    "lab_id": item.lab_id,
                    "lab_name": item.lab_name,
                    "spec": item.spec,
                    "quantity": item.quantity,
                    "status": item.status,
                }
                rows.append(equipment)
            return json.dumps(
                {"total": page.total, "equipments": rows}, ensure_ascii=False
            )

        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def create_lab_reservation(data: ReservationCreateRequest) -> str:
        """创建预约单预约实验室或者设备"""
        try:
            reservation_service.create_reservation(
                db=db, current_user=current_user, data=data
            )
            return json.dumps(
                {
                    "ok": True,
                    "message": "用户已提交，待审核",
                    "lab_id": data.lab_id,
                    "equipment_id": data.equipment_id,
                    "date": data.date,
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                    "remark": data.remark,
                },
                ensure_ascii=False,
            )
        except BusinessException as exc:
            return json.dumps({"ok": False, "error": exc.message}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def get_today() -> str:
        """获取今天的日期"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d")

    return [
        search_lab_docs,
        list_open_labs,
        list_lab_equipments,
        create_lab_reservation,
        get_today,
    ]
