"""
LightRAG多模态集成模块

将图像处理功能集成到现有的LightRAG系统中
扩展文档处理和知识图谱构建能力
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from .image_processor import ImageProcessor, ImageProcessorConfig
from .document_parser import MultimodalDocumentParser
from .vision_models import setup_doubao_vision_model, VisionModelFactory

logger = logging.getLogger(__name__)

class MultimodalLightRAG:
    """多模态LightRAG系统
    
    集成图像处理功能的LightRAG系统
    """
    
    def __init__(self, 
                 lightrag_instance=None,
                 image_processor_config: Optional[ImageProcessorConfig] = None,
                 vision_model_config: Optional[Dict] = None):
        """初始化多模态LightRAG系统
        
        Args:
            lightrag_instance: 现有的LightRAG实例
            image_processor_config: 图像处理器配置
            vision_model_config: 视觉模型配置
        """
        self.lightrag = lightrag_instance
        
        # 创建图像处理器
        self.image_processor = ImageProcessor(image_processor_config)
        
        # 创建文档解析器
        self.document_parser = MultimodalDocumentParser(self.image_processor)
        
        # 设置视觉模型
        self._setup_vision_models(vision_model_config)
        
        # 多模态内容缓存
        self.multimodal_cache = {}
    
    def _setup_vision_models(self, config: Optional[Dict]):
        """设置视觉模型
        
        Args:
            config: 视觉模型配置
        """
        if not config:
            config = {}
        
        # 设置豆包视觉模型
        doubao_config = config.get("doubao", {})
        if doubao_config.get("api_key"):
            try:
                doubao_model = VisionModelFactory.create_doubao_vision_model(
                    api_key=doubao_config["api_key"],
                    model_name=doubao_config.get("model_name", "doubao-1-5-thinking-vision-pro-250428")
                )
                
                self.image_processor.register_vision_model("doubao", doubao_model)
                self.image_processor.register_vision_model("default", doubao_model)
                
                logger.info("豆包视觉模型设置成功")
                
            except Exception as e:
                logger.error(f"设置豆包视觉模型失败: {e}")
        
        # 设置OpenAI视觉模型
        openai_config = config.get("openai", {})
        if openai_config.get("api_key"):
            try:
                openai_model = VisionModelFactory.create_openai_vision_model(
                    api_key=openai_config["api_key"],
                    model_name=openai_config.get("model_name", "gpt-4o"),
                    base_url=openai_config.get("base_url")
                )
                
                self.image_processor.register_vision_model("openai", openai_model)
                self.image_processor.register_vision_model("gpt-4o", openai_model)
                
                logger.info("OpenAI视觉模型设置成功")
                
            except Exception as e:
                logger.error(f"设置OpenAI视觉模型失败: {e}")
    
    async def process_image_file(self, 
                               image_path: Union[str, Path],
                               operations: List[str] = None) -> Dict[str, Any]:
        """处理图像文件
        
        Args:
            image_path: 图像文件路径
            operations: 要执行的操作列表
            
        Returns:
            处理结果
        """
        return await self.image_processor.process_image_file(image_path, operations)
    
    async def process_multimodal_document(self, 
                                        file_path: Union[str, Path]) -> Dict[str, Any]:
        """处理多模态文档
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            处理结果，包含文本和图像内容
        """
        # 检查缓存
        file_key = str(Path(file_path).resolve())
        if file_key in self.multimodal_cache:
            logger.info(f"使用缓存的多模态文档: {file_path}")
            return self.multimodal_cache[file_key]
        
        # 提取多模态内容
        result = await self.document_parser.extract_multimodal_content(file_path)
        
        # 缓存结果
        if "error" not in result:
            self.multimodal_cache[file_key] = result
        
        return result
    
    async def insert_multimodal_document(self, 
                                       file_path: Union[str, Path],
                                       chunk_token_max: int = 1200,
                                       overlap_token_num: int = 100) -> bool:
        """插入多模态文档到LightRAG系统
        
        Args:
            file_path: 文档文件路径
            chunk_token_max: 最大分块token数
            overlap_token_num: 重叠token数
            
        Returns:
            是否插入成功
        """
        if not self.lightrag:
            logger.error("LightRAG实例未设置")
            return False
        
        try:
            # 处理多模态文档
            multimodal_content = await self.process_multimodal_document(file_path)
            
            if "error" in multimodal_content:
                logger.error(f"处理多模态文档失败: {multimodal_content['error']}")
                return False
            
            # 获取合并的内容
            combined_content = multimodal_content.get("combined_content", "")
            
            if not combined_content.strip():
                logger.warning("文档内容为空")
                return False
            
            # 插入到LightRAG系统
            await self.lightrag.ainsert(combined_content)
            
            logger.info(f"多模态文档插入成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"插入多模态文档失败: {e}")
            return False
    
    async def query_with_multimodal_context(self, 
                                          query: str,
                                          mode: str = "hybrid",
                                          only_need_context: bool = False) -> str:
        """使用多模态上下文进行查询
        
        Args:
            query: 查询问题
            mode: 查询模式 ("naive", "local", "global", "hybrid")
            only_need_context: 是否只需要上下文
            
        Returns:
            查询结果
        """
        if not self.lightrag:
            return "LightRAG实例未设置"
        
        try:
            # 使用LightRAG进行查询
            result = await self.lightrag.aquery(
                query=query,
                param={"mode": mode, "only_need_context": only_need_context}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"多模态查询失败: {e}")
            return f"查询失败: {str(e)}"
    
    async def batch_insert_multimodal_documents(self, 
                                              file_paths: List[Union[str, Path]],
                                              max_concurrent: int = 3) -> Dict[str, Any]:
        """批量插入多模态文档
        
        Args:
            file_paths: 文档文件路径列表
            max_concurrent: 最大并发数
            
        Returns:
            批量处理结果
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def insert_single_document(file_path):
            async with semaphore:
                success = await self.insert_multimodal_document(file_path)
                return {
                    "file_path": str(file_path),
                    "success": success
                }
        
        tasks = [insert_single_document(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        successful = 0
        failed = 0
        errors = []
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                error_result = {
                    "file_path": str(file_paths[i]),
                    "success": False,
                    "error": str(result)
                }
                errors.append(error_result)
                processed_results.append(error_result)
            else:
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
                processed_results.append(result)
        
        return {
            "total": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": processed_results,
            "errors": errors
        }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式
        
        Returns:
            支持的格式字典
        """
        return {
            "images": self.image_processor.get_supported_formats(),
            "documents": list(self.document_parser.supported_formats.keys())
        }
    
    def clear_cache(self):
        """清空缓存"""
        # 清空图像处理缓存
        self.image_processor.clear_cache()
        
        # 清空多模态内容缓存
        self.multimodal_cache.clear()
        
        logger.info("多模态缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        stats = {
            "multimodal_documents": len(self.multimodal_cache),
            "image_cache_dir": self.image_processor.config.cache_dir
        }
        
        # 统计图像缓存文件
        cache_dir = Path(self.image_processor.config.cache_dir)
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.json"))
            stats["image_cache_files"] = len(cache_files)
        else:
            stats["image_cache_files"] = 0
        
        return stats

def create_multimodal_lightrag(lightrag_instance=None,
                             doubao_api_key: str = None,
                             openai_api_key: str = None,
                             openai_base_url: str = None,
                             image_config: Dict = None) -> MultimodalLightRAG:
    """创建多模态LightRAG实例
    
    Args:
        lightrag_instance: 现有的LightRAG实例
        doubao_api_key: 豆包API密钥
        openai_api_key: OpenAI API密钥
        openai_base_url: OpenAI API基础URL
        image_config: 图像处理配置
        
    Returns:
        多模态LightRAG实例
    """
    # 准备图像处理器配置
    if image_config is None:
        image_config = {}
    
    image_processor_config = ImageProcessorConfig(**image_config)
    
    # 准备视觉模型配置
    vision_model_config = {}
    
    if doubao_api_key:
        vision_model_config["doubao"] = {
            "api_key": doubao_api_key,
            "model_name": "doubao-1-5-thinking-vision-pro-250428"
        }
    
    if openai_api_key:
        openai_config = {"api_key": openai_api_key}
        if openai_base_url:
            openai_config["base_url"] = openai_base_url
        vision_model_config["openai"] = openai_config
    
    # 创建多模态LightRAG实例
    return MultimodalLightRAG(
        lightrag_instance=lightrag_instance,
        image_processor_config=image_processor_config,
        vision_model_config=vision_model_config
    )