# 禁用知识图谱功能 - 注释掉整个模块
"""
This module contains all graph-related routes for the LightRAG API.
已禁用 - 所有知识图谱相关的API端点已被注释掉
"""

# from typing import Optional, Dict, Any
# import traceback
# from fastapi import APIRouter, Depends, Query, HTTPException
# from pydantic import BaseModel

# from lightrag.utils import logger
# from ..utils_api import get_combined_auth_dependency

# router = APIRouter(tags=["graph"])

# 禁用所有知识图谱相关的类和函数定义
# class EntityUpdateRequest(BaseModel):
#     entity_name: str
#     updated_data: Dict[str, Any]
#     allow_rename: bool = False

# class RelationUpdateRequest(BaseModel):
#     source_id: str
#     target_id: str
#     updated_data: Dict[str, Any]

# def create_graph_routes(rag, api_key: Optional[str] = None):
#     """
#     创建知识图谱相关的路由 - 已禁用
#     """
#     pass
#     # 所有知识图谱API端点已被注释掉
#     # return router
