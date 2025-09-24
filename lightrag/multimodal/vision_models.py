"""
视觉模型工厂和集成模块

提供统一的视觉模型接口和豆包视觉模型集成
"""

import os
import json
import base64
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 全局视觉模型注册表
_vision_models: Dict[str, Callable] = {}

def register_vision_model(name: str, model_func: Callable):
    """注册视觉模型
    
    Args:
        name: 模型名称
        model_func: 模型函数
    """
    _vision_models[name] = model_func
    logger.info(f"注册视觉模型: {name}")

def get_vision_model(name: str) -> Optional[Callable]:
    """获取视觉模型
    
    Args:
        name: 模型名称
        
    Returns:
        模型函数或None
    """
    return _vision_models.get(name)

def list_vision_models() -> List[str]:
    """列出所有已注册的视觉模型
    
    Returns:
        模型名称列表
    """
    return list(_vision_models.keys())

class VisionModelFactory:
    """视觉模型工厂"""
    
    @staticmethod
    def create_doubao_vision_model(api_key: str, 
                                 model_name: str = "doubao-1-5-thinking-vision-pro-250428",
                                 base_url: str = "https://ark.cn-beijing.volces.com/api/v3") -> Callable:
        """创建豆包视觉模型
        
        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API基础URL
            
        Returns:
            豆包视觉模型函数
        """
        try:
            from volcenginesdkarkruntime import Ark
        except ImportError:
            logger.error("请安装volcengine-python-sdk: pip install volcengine-python-sdk")
            raise ImportError("volcengine-python-sdk is required for Doubao vision model")
        
        # 创建Ark客户端
        client = Ark(api_key=api_key, base_url=base_url)
        
        async def doubao_vision_func(image_data: bytes, prompt: str = "请描述这张图片") -> Dict[str, Any]:
            """豆包视觉模型函数
            
            Args:
                image_data: 图像二进制数据
                prompt: 提示词
                
            Returns:
                分析结果
            """
            try:
                # 将图像编码为base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_base64}"
                
                # 构建消息
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
                
                # 调用API
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.1
                )
                
                # 提取结果
                if completion.choices and len(completion.choices) > 0:
                    content = completion.choices[0].message.content
                    
                    return {
                        "content": content,
                        "model": model_name,
                        "timestamp": datetime.now().isoformat(),
                        "usage": {
                            "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                            "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                            "total_tokens": completion.usage.total_tokens if completion.usage else 0
                        }
                    }
                else:
                    logger.error("豆包API返回空结果")
                    return {"error": "API返回空结果"}
                    
            except Exception as e:
                logger.error(f"豆包视觉模型调用失败: {e}")
                return {"error": str(e)}
        
        return doubao_vision_func
    
    @staticmethod
    def create_openai_vision_model(api_key: str,
                                 model_name: str = "gpt-4o",
                                 base_url: Optional[str] = None) -> Callable:
        """创建OpenAI视觉模型
        
        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API基础URL
            
        Returns:
            OpenAI视觉模型函数
        """
        try:
            import openai
        except ImportError:
            logger.error("请安装openai库: pip install openai")
            raise ImportError("openai is required for OpenAI vision model")
        
        # 创建OpenAI客户端
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        client = openai.AsyncOpenAI(**client_kwargs)
        
        async def openai_vision_func(image_data: bytes, prompt: str = "请描述这张图片") -> Dict[str, Any]:
            """OpenAI视觉模型函数
            
            Args:
                image_data: 图像二进制数据
                prompt: 提示词
                
            Returns:
                分析结果
            """
            try:
                # 将图像编码为base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_base64}"
                
                # 构建消息
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
                
                # 调用API
                completion = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.1
                )
                
                # 提取结果
                if completion.choices and len(completion.choices) > 0:
                    content = completion.choices[0].message.content
                    
                    return {
                        "content": content,
                        "model": model_name,
                        "timestamp": datetime.now().isoformat(),
                        "usage": {
                            "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                            "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                            "total_tokens": completion.usage.total_tokens if completion.usage else 0
                        }
                    }
                else:
                    logger.error("OpenAI API返回空结果")
                    return {"error": "API返回空结果"}
                    
            except Exception as e:
                logger.error(f"OpenAI视觉模型调用失败: {e}")
                return {"error": str(e)}
        
        return openai_vision_func

def setup_doubao_vision_model(api_key: str = None):
    """设置豆包视觉模型
    
    Args:
        api_key: API密钥，如果为None则从环境变量获取
    """
    if api_key is None:
        api_key = os.getenv("DOUBAO_API_KEY")
    
    if not api_key:
        logger.error("未提供豆包API密钥")
        return False
    
    try:
        # 创建豆包视觉模型
        doubao_model = VisionModelFactory.create_doubao_vision_model(api_key)
        
        # 注册模型
        register_vision_model("doubao", doubao_model)
        register_vision_model("default", doubao_model)  # 设为默认模型
        
        logger.info("豆包视觉模型设置成功")
        return True
        
    except Exception as e:
        logger.error(f"设置豆包视觉模型失败: {e}")
        return False

def setup_openai_vision_model(api_key: str = None, base_url: str = None):
    """设置OpenAI视觉模型
    
    Args:
        api_key: API密钥，如果为None则从环境变量获取
        base_url: API基础URL
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("未提供OpenAI API密钥")
        return False
    
    try:
        # 创建OpenAI视觉模型
        openai_model = VisionModelFactory.create_openai_vision_model(api_key, base_url=base_url)
        
        # 注册模型
        register_vision_model("openai", openai_model)
        register_vision_model("gpt-4o", openai_model)
        
        logger.info("OpenAI视觉模型设置成功")
        return True
        
    except Exception as e:
        logger.error(f"设置OpenAI视觉模型失败: {e}")
        return False

async def test_vision_model(model_name: str, test_image_path: str) -> Dict[str, Any]:
    """测试视觉模型
    
    Args:
        model_name: 模型名称
        test_image_path: 测试图像路径
        
    Returns:
        测试结果
    """
    model_func = get_vision_model(model_name)
    if not model_func:
        return {"error": f"未找到模型: {model_name}"}
    
    try:
        # 读取测试图像
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        # 测试图像分析
        result = await model_func(image_data, "请描述这张图片的内容")
        
        return {
            "model": model_name,
            "test_image": test_image_path,
            "result": result,
            "success": "error" not in result
        }
        
    except Exception as e:
        return {
            "model": model_name,
            "test_image": test_image_path,
            "error": str(e),
            "success": False
        }