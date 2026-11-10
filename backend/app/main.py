import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, staticfiles
import fastapi
from fastapi.exceptions import RequestValidationError
from app.models.user import User
from app.api import api
from starlette.middleware.cors import CORSMiddleware
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import Base, engine
from app.common.exception import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.config import UPLOAD_DIR
from app.models.lab import Lab
from app.services import kb_service, reservation_service

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 预热向量库：模型加载（约 15s）挪到启动阶段，避免拖慢首个请求、触发前端超时
    try:
        await asyncio.to_thread(kb_service.warmup)
    except Exception:
        logger.exception("向量库预热失败，服务继续启动")
    # 启动项目开启异步的扫描任务
    task = asyncio.create_task(reservation_service.run_expire_scan())
    yield
    task.cancel()  ## 关闭项目同时取消异步任务


app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)
app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# 全局的异常兜底，必须放在最后注册！！
app.add_exception_handler(Exception, global_exception_handler)
# 挂载静态的文件目录
app.mount("/uploads", staticfiles.StaticFiles(directory=UPLOAD_DIR), name="uploads")
# 兼容历史记录中保存的 /upload/ 图片地址，新上传仍返回 /uploads/。
app.mount("/upload", staticfiles.StaticFiles(directory=UPLOAD_DIR), name="legacy_uploads")


@app.get("/")
def root():
    return {"message": "Fastapi工程真正启动"}
