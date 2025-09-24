"""
This module contains all the routers for the LightRAG API.
"""

from .document_routes import router as document_router
from .query_routes import router as query_router
# 禁用知识图谱功能 - 注释掉图路由导入
# from .graph_routes import router as graph_router
from .ollama_api import OllamaAPI

# 禁用知识图谱功能 - 从导出列表中移除graph_router
__all__ = ["document_router", "query_router", "OllamaAPI"]
