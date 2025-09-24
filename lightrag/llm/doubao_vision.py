"""
豆包视觉模型适配器

实现豆包(Doubao) Vision Pro模型的图像理解和OCR功能
支持多模态内容处理，包括图像分析、文本识别和内容理解
"""

import os
import base64
import asyncio
from typing import Dict, List, Optional, Union, Any
import httpx
import json
from PIL import Image
import io

from ..base import BaseKVStorage
from ..utils import logger


class DoubaoVisionLLM:
    """豆包视觉模型适配器类"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-1-5-thinking-vision-pro-250428",
        max_tokens: int = 4000,
        temperature: float = 0.1,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化豆包视觉模型
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 设置HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.aclose()
    
    def _encode_image(self, image_path: str) -> str:
        """
        将图像文件编码为base64字符串
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            base64编码的图像字符串
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图像编码失败: {e}")
            raise
    
    def _prepare_image_content(self, image_data: Union[str, bytes]) -> str:
        """
        准备图像内容，支持文件路径、base64字符串或字节数据
        
        Args:
            image_data: 图像数据（文件路径、base64字符串或字节）
            
        Returns:
            base64编码的图像字符串
        """
        if isinstance(image_data, str):
            if os.path.exists(image_data):
                # 文件路径
                return self._encode_image(image_data)
            else:
                # 假设是base64字符串
                return image_data
        elif isinstance(image_data, bytes):
            # 字节数据
            return base64.b64encode(image_data).decode('utf-8')
        else:
            raise ValueError(f"不支持的图像数据类型: {type(image_data)}")
    
    async def _make_request(self, messages: List[Dict], **kwargs) -> Dict:
        """
        发送API请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            API响应结果
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
            
            except Exception as e:
                logger.error(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def analyze_image(
        self,
        image_data: Union[str, bytes],
        prompt: str = "请详细描述这张图片的内容，包括主要对象、场景、文字信息等。",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        分析图像内容
        
        Args:
            image_data: 图像数据（文件路径、base64字符串或字节）
            prompt: 分析提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            图像分析结果
        """
        try:
            # 准备图像内容
            image_base64 = self._prepare_image_content(image_data)
            
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            })
            
            # 发送请求
            response = await self._make_request(messages, **kwargs)
            
            # 提取结果
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                raise ValueError("API响应格式错误")
                
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            raise
    
    async def extract_text_from_image(
        self,
        image_data: Union[str, bytes],
        prompt: str = "请提取图片中的所有文字内容，保持原有格式和结构。",
        **kwargs
    ) -> str:
        """
        从图像中提取文字（OCR功能）
        
        Args:
            image_data: 图像数据
            prompt: OCR提示词
            **kwargs: 其他参数
            
        Returns:
            提取的文字内容
        """
        system_prompt = (
            "你是一个专业的OCR助手，专门负责从图像中准确提取文字内容。"
            "请仔细识别图片中的所有文字，包括标题、正文、表格、标签等，"
            "并保持原有的格式和结构。如果有表格，请用markdown格式输出。"
        )
        
        return await self.analyze_image(
            image_data=image_data,
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def understand_document_image(
        self,
        image_data: Union[str, bytes],
        prompt: str = "请分析这个文档图片，提取关键信息并总结主要内容。",
        **kwargs
    ) -> Dict[str, str]:
        """
        理解文档图像，提取结构化信息
        
        Args:
            image_data: 图像数据
            prompt: 理解提示词
            **kwargs: 其他参数
            
        Returns:
            包含文档分析结果的字典
        """
        system_prompt = (
            "你是一个专业的文档分析助手。请分析文档图片并提供以下信息：\n"
            "1. 文档类型和主题\n"
            "2. 关键信息摘要\n"
            "3. 重要实体（人名、地名、机构名、日期等）\n"
            "4. 文档结构分析\n"
            "5. 完整的文字内容\n"
            "请用JSON格式返回结果。"
        )
        
        try:
            result = await self.analyze_image(
                image_data=image_data,
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            
            # 尝试解析JSON结果
            try:
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError:
                # 如果不是JSON格式，返回原始结果
                return {
                    "analysis": result,
                    "raw_content": result
                }
                
        except Exception as e:
            logger.error(f"文档图像理解失败: {e}")
            raise
    
    async def batch_analyze_images(
        self,
        image_list: List[Union[str, bytes]],
        prompt: str = "请分析这张图片的内容。",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        批量分析多张图像
        
        Args:
            image_list: 图像数据列表
            prompt: 分析提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            分析结果列表
        """
        tasks = []
        for image_data in image_list:
            task = self.analyze_image(
                image_data=image_data,
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"图像 {i} 分析失败: {result}")
                processed_results.append(f"分析失败: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results


# 便捷函数
async def create_doubao_vision_llm(
    api_key: Optional[str] = None,
    **kwargs
) -> DoubaoVisionLLM:
    """
    创建豆包视觉模型实例
    
    Args:
        api_key: API密钥，如果为None则从环境变量获取
        **kwargs: 其他参数
        
    Returns:
        DoubaoVisionLLM实例
    """
    if api_key is None:
        api_key = os.getenv("DOUBAO_API_KEY")
        if not api_key:
            raise ValueError("请提供API密钥或设置DOUBAO_API_KEY环境变量")
    
    return DoubaoVisionLLM(api_key=api_key, **kwargs)


# 兼容LightRAG的函数接口
async def doubao_vision_complete(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[Dict]] = None,
    image_data: Optional[Union[str, bytes]] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """
    豆包视觉模型完成函数，兼容LightRAG接口
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        history_messages: 历史消息
        image_data: 图像数据
        api_key: API密钥
        **kwargs: 其他参数
        
    Returns:
        模型响应结果
    """
    if api_key is None:
        api_key = os.getenv("DOUBAO_API_KEY", "6674bc28-fc4b-47b8-8795-bf79eb01c9ff")
    
    async with DoubaoVisionLLM(api_key=api_key, **kwargs) as llm:
        if image_data:
            return await llm.analyze_image(
                image_data=image_data,
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
        else:
            # 纯文本模式，构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史消息
            if history_messages:
                messages.extend(history_messages)
            
            messages.append({"role": "user", "content": prompt})
            
            response = await llm._make_request(messages, **kwargs)
            
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                raise ValueError("API响应格式错误")