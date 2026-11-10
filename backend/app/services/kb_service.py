from chromadb import Collection
import chromadb
from app.config import BASE_DIR
from chromadb.utils import embedding_functions

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
_collection = None
_embedding_fn = None


def get_embedding_fn():
    """懒加载Embedding模型"""
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn
    # ① 初始化 Embedding 模型
    _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5"
    )
    return _embedding_fn


def warmup():
    """启动时预热：把模型加载 + 首次检索的开销付在启动阶段，别落在第一个用户请求上"""

    col = get_collection()
    if col.count() > 0:
        col.query(query_texts=["预热"], n_results=1)


def get_collection() -> Collection:
    """向量库初始化"""
    global _collection
    # 如果已经初始化过，直接返回
    if _collection is not None:
        return _collection
    # 确保知识库文件夹和向量数据库文件夹存在
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    # ② 连接 ChromaDB 数据库
    client = chromadb.PersistentClient(path=(str(CHROMA_DIR)))
    # ③ 获取或创建 lab_kb 知识库
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=get_embedding_fn()
    )
    # ④ 如果知识库为空，导入 Markdown 文档
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        # 遍历 data/db 文件夹下的所有 .md 文件
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="UTF-8").strip()
            if not text:
                continue
            if text:
                # 保存文档ID、内容、来源信息
                ids.append(path.stem)
                docs.append(text)
                metas.append({"source": path.name})
        # 将文档写入 ChromaDB，并自动生成向量
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)
    # 缓存 Collection，后续直接复用
    _collection = col
    return col


def search(query: str):
    col = get_collection()
    if col.count() == 0:
        return ""
    limit = min(5, col.count())
    res = col.query(query_texts=[query], n_results=limit)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]
    score_parts = []
    for doc, meta, dist in zip(docs, metas, distances):
        score = 1 / (1 + dist)
        if score < 0.5:
            continue
        name = meta.get("source") or ""
        score_parts.append({"score": score, "content": f"{name}\n{doc}"})
    print(f"检验出来的score_parts:{score_parts}")
    score_parts.sort(key=lambda x: x["score"], reverse=True)
    final_part = [item["content"] for item in score_parts[0:2]]
    return "\n\n".join(final_part)
