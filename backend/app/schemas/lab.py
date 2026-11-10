from pydantic import BaseModel, ConfigDict


class LabResponse(BaseModel):
    id: int
    name: str
    location: str | None
    capacity: int
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int
    model_config = ConfigDict(
        from_attributes=True
    )  # 告诉 Pydantic：允许从对象的属性中读取数据，而不只是从字典中读取数据


class LabCreateRequest(BaseModel):
    name: str
    location: str | None = None
    capacity: int = 0
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int = 1


class LabUpdateRequest(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int | None = None
