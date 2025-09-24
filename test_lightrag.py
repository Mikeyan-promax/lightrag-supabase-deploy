#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LightRAG 基本功能测试脚本
使用 Ollama 和 PostgreSQL 进行 RAG 演示
"""

import asyncio
import os
import logging
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=".env", override=False)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 工作目录
WORKING_DIR = "./lightrag_test"

# 确保工作目录存在
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

async def test_lightrag():
    """
    测试 LightRAG 基本功能
    """
    try:
        logger.info("开始初始化 LightRAG...")
        
        # 初始化 LightRAG 实例
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=ollama_model_complete,
            llm_model_name="llama3.2:latest",
            summary_max_tokens=4096,
            llm_model_kwargs={
                "host": "http://localhost:11434",
                "options": {"num_ctx": 4096},
                "timeout": 300,
            },
            embedding_func=EmbeddingFunc(
                embedding_dim=1024,
                max_token_size=4096,
                func=lambda texts: ollama_embed(
                    texts,
                    embed_model="bge-m3:latest",
                    host="http://localhost:11434",
                ),
            ),
        )
        
        logger.info("初始化存储系统...")
        await rag.initialize_storages()
        
        logger.info("测试嵌入功能...")
        # 测试嵌入功能
        test_text = ["这是一个测试文本用于嵌入。"]
        try:
            embedding = await rag.embedding_func(test_text)
            logger.info(f"嵌入测试成功，维度: {embedding.shape}")
        except Exception as e:
            logger.error(f"嵌入测试失败: {e}")
            return False
        
        # 检查是否有测试文件
        if os.path.exists("./book.txt"):
            logger.info("读取测试文件 book.txt...")
            with open("./book.txt", "r", encoding="utf-8") as f:
                content = f.read()[:2000]  # 只读取前2000字符进行测试
                logger.info(f"文件内容长度: {len(content)} 字符")
                
            logger.info("插入文档到 RAG 系统...")
            await rag.ainsert(content)
            logger.info("文档插入成功")
            
            # 测试查询
            logger.info("测试查询功能...")
            query = "这个故事的主要主题是什么？"
            
            logger.info("执行 naive 模式查询...")
            resp = await rag.aquery(
                query,
                param=QueryParam(mode="naive")
            )
            logger.info(f"Naive 查询结果: {resp[:200]}...")
            
        else:
            logger.warning("未找到 book.txt 文件，跳过文档测试")
            
            # 使用简单文本进行测试
            test_content = """
            人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
            机器学习是人工智能的一个子集，它使计算机能够从数据中学习而无需明确编程。
            深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。
            """
            
            logger.info("使用测试文本进行演示...")
            await rag.ainsert(test_content)
            
            query = "什么是人工智能？"
            resp = await rag.aquery(
                query,
                param=QueryParam(mode="naive")
            )
            logger.info(f"查询结果: {resp}")
        
        logger.info("LightRAG 基本功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理资源
        try:
            if 'rag' in locals():
                await rag.finalize_storages()
                logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理时发生错误: {e}")

if __name__ == "__main__":
    logger.info("开始 LightRAG 测试...")
    success = asyncio.run(test_lightrag())
    if success:
        logger.info("✅ 测试成功完成！")
    else:
        logger.error("❌ 测试失败！")
    print("\n测试完成！")