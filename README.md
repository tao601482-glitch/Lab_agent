# 智能实验室预约系统

基于 FastAPI、Vue 3、LangGraph 和 ChromaDB 的个人实践项目，
支持实验室与设备查询、预约申请、管理员审核以及 AI 辅助预约。

## 主要功能

- 实验室与设备信息查询
- 预约申请、预约记录查询与管理员审核
- 基于知识库的规则问答
- 通过 AI 工具调用查询资源、提交预约
- 展示 AI 流式回答与工具执行状态

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy
- 前端：Vue 3、Element Plus
- AI：LangGraph、ChromaDB、BGE 中文向量模型
- 认证与交互：JWT、SSE
