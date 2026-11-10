from json import JSONDecodeError, load
import json

from sqlalchemy.orm import Session
from app.common.exception import BusinessException
from openai import OpenAI
from app.config import settings
from app.schemas.ai import ChatRequest
from app.schemas.ai import ChatMessage
from app.services import kb_service
from app.services.equipment_service import get_equipment_page_list
from app.services.lab_service import get_lab_page_list

# 系统提示词
SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答规则、安全、文档里的开放时间说明。
查询当前有哪些开放实验室、某实验室有哪些设备时，必须调用工具，不要编造。
你不能替用户提交预约，也不能直接改数据库。
如果用户要预约，请说明去「实验室列表」选择后提交，等待管理员审核。
"""

TOOL = [
    {
        "type": "function",
        "function": {
            "name": "list_open_labs",
            "description": "查询当前开放中的实验室列表,可以按名称关键字来筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "实验室的名称关键字,可以为空",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_lab_equipment",
            "description": "查询某个实验室下的设备列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_id": {"type": "integer", "description": "实验室ID"},
                    "keywords": {
                        "type": "string",
                        "description": "设备名称的关键字可以为空",
                    },
                },
                "required": ["lab_id"],
            },
        },
    },
]


def run_tool(db: Session, name: str, argument: str):
    try:
        args = json.loads(argument or "{}")
    except json.JSONDecodeError:

        return json.dumps({"error": "参数不合法的json"}, ensure_ascii=False)
    try:
        if name == "list_open_labs":
            keyword = (args.get("keywords") or "").strip() or None
            page = get_lab_page_list(
                db=db, page=1, page_size=10, keywords=keyword, status=1
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
            return json.dumps({"total": page.total, "lab": rows}, ensure_ascii=False)
        if name == "list_lab_equipment":
            lab_id = args.get("lab_id")
            if not lab_id:
                return json.dumps({"error": "参数缺少实验室lab_id"}, ensure_ascii=False)
            keywords = (args.get("keywords") or "").strip() or None
            page = get_equipment_page_list(
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
                {"total": page.total, "equipment": rows}, ensure_ascii=False
            )
        return json.dumps({"error": f"未找到工具{name}"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": exc.message}, ensure_ascii=False)


# 创建客户端
def get_client() -> OpenAI:
    if not settings.LLM_API_KEY:
        raise BusinessException(message="未获取到大模型的APIKey")
    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def chat(db: Session, data: ChatRequest):
    # 1.检查用户信息
    if not data.messages:
        raise BusinessException(message="对话内容为空")
    # 2.整理历史消息
    history = []
    for message in data.messages:
        if (
            message.role in ["user", "assistant"] and message.content.strip()
        ):  # strip 去除两端空白
            history.append(message.model_dump())
    if not history:
        raise BusinessException(message="请输入你要对话的内容")
    # 3.取出用户提出的最后一个问题
    question = ""
    for item in reversed(history):
        if item["role"] == "user":
            question = item["content"]
            break
    # 4.检索知识库
    knowledge = kb_service.search(query=question)
    print(f"以下是检索到的知识库资料:{knowledge}")
    system_prompt = SYSTEM_PROMPT
    if knowledge:
        system_prompt += "\n\n以下是检索到的知识库资料:\n" + knowledge
    # 5.创建客户端
    client = get_client()
    # 6.构造消息列表
    messages = [{"role": "system", "content": system_prompt}, *history]
    # 7.最多进行三轮模型请求
    try:
        for _ in range(3):
            res = client.chat.completions.create(  # completions根据你提供的消息，让模型继续生成合适的内容。
                model=settings.LLM_MODEL,
                messages=messages,
                tools=TOOL,
                tool_choice="auto",
            )
            # 8.获取大模型回复
            msg = res.choices[0].message
            tool_calls = msg.tool_calls or []
            # 9.如果不需要工具直接返回
            if not tool_calls:
                content = msg.content
                if not content or not content.strip():
                    raise BusinessException(message="大模型没有返回内容")
                return content
            # 整理模型的工具调用请求
            calls = []
            for call in tool_calls:
                call_data = {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                calls.append(call_data)
            # 保存assistant工具调用信息
            messages.append(
                {"role": "assistant", "content": msg.content or "", "tool_calls": calls}
            )
            # 执行工具
            for call in tool_calls:
                result = run_tool(
                    db=db, name=call.function.name, argument=call.function.arguments
                )
                # 保存工具结果
                messages.append(
                    {"role": "tool", "content": result, "tool_call_id": call.id}
                )
        # # 14. 三轮结束后，强制尝试生成最终回答
        res = client.chat.completions.create(
            model=settings.LLM_MODEL, messages=messages, tools=TOOL, tool_choice="none"
        )
        content = res.choices[0].message.content
        if not content or not content.strip():
            raise BusinessException(message="大模型没有返回信息")
        return content

    except BusinessException:
        raise
    except Exception:
        raise BusinessException(message="大模型调用失败，没有返回内容")
