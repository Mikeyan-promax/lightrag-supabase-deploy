"""
图像处理核心模块

提供图像预处理、OCR、内容理解等功能
支持多种图片格式和视觉模型
"""

import os
import base64
import hashlib
import asyncio
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    from PIL import Image
    import io
except ImportError:
    Image = None
    io = None

logger = logging.getLogger(__name__)

@dataclass
class ImageProcessorConfig:
    """图像处理器配置"""
    # 支持的图片格式
    supported_formats: List[str] = None
    # 最大图片尺寸
    max_image_size: Tuple[int, int] = (2048, 2048)
    # 图片质量
    image_quality: int = 85
    # 缓存目录
    cache_dir: Optional[str] = None
    # 是否启用缓存
    enable_cache: bool = True
    # OCR语言
    ocr_languages: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp']
        if self.ocr_languages is None:
            self.ocr_languages = ['zh', 'en']
        if self.cache_dir is None:
            self.cache_dir = os.path.join(os.getcwd(), '.lightrag_cache', 'images')

class ImageProcessor:
    """图像处理器
    
    提供图像预处理、OCR、内容理解等功能
    """
    
    def __init__(self, config: Optional[ImageProcessorConfig] = None):
        """初始化图像处理器
        
        Args:
            config: 图像处理器配置
        """
        self.config = config or ImageProcessorConfig()
        self.vision_models = {}
        self._setup_cache_dir()
        
    def _setup_cache_dir(self):
        """设置缓存目录"""
        if self.config.enable_cache and self.config.cache_dir:
            os.makedirs(self.config.cache_dir, exist_ok=True)
    
    def register_vision_model(self, name: str, model_func):
        """注册视觉模型
        
        Args:
            name: 模型名称
            model_func: 模型函数，接受图像数据和提示词，返回分析结果
        """
        self.vision_models[name] = model_func
        logger.info(f"注册视觉模型: {name}")
    
    def _get_image_hash(self, image_data: bytes) -> str:
        """获取图像哈希值用于缓存
        
        Args:
            image_data: 图像二进制数据
            
        Returns:
            图像哈希值
        """
        return hashlib.md5(image_data).hexdigest()
    
    def _get_cache_path(self, image_hash: str, operation: str) -> str:
        """获取缓存文件路径
        
        Args:
            image_hash: 图像哈希值
            operation: 操作类型 (ocr, analysis, etc.)
            
        Returns:
            缓存文件路径
        """
        return os.path.join(self.config.cache_dir, f"{image_hash}_{operation}.json")
    
    def _load_cache(self, cache_path: str) -> Optional[Dict]:
        """加载缓存数据
        
        Args:
            cache_path: 缓存文件路径
            
        Returns:
            缓存数据或None
        """
        if not self.config.enable_cache or not os.path.exists(cache_path):
            return None
            
        try:
            import json
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None
    
    def _save_cache(self, cache_path: str, data: Dict):
        """保存缓存数据
        
        Args:
            cache_path: 缓存文件路径
            data: 要缓存的数据
        """
        if not self.config.enable_cache:
            return
            
        try:
            import json
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def load_image(self, image_path: Union[str, Path]) -> Optional[bytes]:
        """加载图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像二进制数据或None
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"图像文件不存在: {image_path}")
                return None
                
            # 检查文件格式
            file_ext = image_path.suffix.lower().lstrip('.')
            if file_ext not in self.config.supported_formats:
                logger.error(f"不支持的图像格式: {file_ext}")
                return None
            
            with open(image_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"加载图像失败: {e}")
            return None
    
    def preprocess_image(self, image_data: bytes) -> Optional[bytes]:
        """预处理图像
        
        Args:
            image_data: 原始图像数据
            
        Returns:
            处理后的图像数据或None
        """
        if not Image or not io:
            logger.warning("PIL库未安装，跳过图像预处理")
            return image_data
            
        try:
            # 打开图像
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 调整尺寸
            if image.size[0] > self.config.max_image_size[0] or image.size[1] > self.config.max_image_size[1]:
                image.thumbnail(self.config.max_image_size, Image.Resampling.LANCZOS)
                logger.info(f"图像尺寸调整为: {image.size}")
            
            # 保存处理后的图像
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.config.image_quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            return image_data
    
    def encode_image_base64(self, image_data: bytes) -> str:
        """将图像编码为base64字符串
        
        Args:
            image_data: 图像二进制数据
            
        Returns:
            base64编码的图像字符串
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    async def analyze_image(self, 
                          image_data: bytes, 
                          prompt: str = "请描述这张图片的内容",
                          model_name: str = "default") -> Optional[Dict]:
        """分析图像内容
        
        Args:
            image_data: 图像二进制数据
            prompt: 分析提示词
            model_name: 使用的视觉模型名称
            
        Returns:
            分析结果字典
        """
        try:
            # 检查缓存
            image_hash = self._get_image_hash(image_data)
            cache_key = f"analysis_{hashlib.md5(prompt.encode()).hexdigest()}"
            cache_path = self._get_cache_path(image_hash, cache_key)
            
            cached_result = self._load_cache(cache_path)
            if cached_result:
                logger.info("使用缓存的图像分析结果")
                return cached_result
            
            # 预处理图像
            processed_image = self.preprocess_image(image_data)
            if not processed_image:
                return None
            
            # 获取视觉模型
            if model_name not in self.vision_models:
                logger.error(f"未找到视觉模型: {model_name}")
                return None
            
            vision_model = self.vision_models[model_name]
            
            # 调用视觉模型
            result = await vision_model(processed_image, prompt)
            
            # 缓存结果
            if result:
                self._save_cache(cache_path, result)
            
            return result
            
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            return None
    
    async def extract_text(self, 
                          image_data: bytes,
                          model_name: str = "default") -> Optional[str]:
        """从图像中提取文本(OCR)
        
        Args:
            image_data: 图像二进制数据
            model_name: 使用的视觉模型名称
            
        Returns:
            提取的文本内容
        """
        try:
            # 检查缓存
            image_hash = self._get_image_hash(image_data)
            cache_path = self._get_cache_path(image_hash, "ocr")
            
            cached_result = self._load_cache(cache_path)
            if cached_result:
                logger.info("使用缓存的OCR结果")
                return cached_result.get("text", "")
            
            # 使用图像分析功能进行OCR
            ocr_prompt = "请提取图片中的所有文字内容，保持原有格式和结构。如果没有文字，请返回空字符串。"
            result = await self.analyze_image(image_data, ocr_prompt, model_name)
            
            if result and "content" in result:
                text_content = result["content"]
                
                # 缓存OCR结果
                ocr_result = {"text": text_content, "timestamp": result.get("timestamp")}
                self._save_cache(cache_path, ocr_result)
                
                return text_content
            
            return ""
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return ""
    
    async def process_image_file(self, 
                               image_path: Union[str, Path],
                               operations: List[str] = None) -> Dict[str, Any]:
        """处理图像文件
        
        Args:
            image_path: 图像文件路径
            operations: 要执行的操作列表 ['ocr', 'analysis', 'description']
            
        Returns:
            处理结果字典
        """
        if operations is None:
            operations = ['ocr', 'analysis']
        
        # 加载图像
        image_data = self.load_image(image_path)
        if not image_data:
            return {"error": "无法加载图像文件"}
        
        results = {
            "file_path": str(image_path),
            "file_size": len(image_data),
            "operations": {}
        }
        
        try:
            # 执行OCR
            if 'ocr' in operations:
                text_content = await self.extract_text(image_data)
                results["operations"]["ocr"] = {
                    "text": text_content,
                    "success": bool(text_content)
                }
            
            # 执行图像分析
            if 'analysis' in operations:
                analysis_result = await self.analyze_image(image_data)
                results["operations"]["analysis"] = analysis_result or {"error": "分析失败"}
            
            # 执行图像描述
            if 'description' in operations:
                description_prompt = "请详细描述这张图片，包括主要内容、颜色、构图、风格等特征。"
                description_result = await self.analyze_image(image_data, description_prompt)
                results["operations"]["description"] = description_result or {"error": "描述失败"}
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"处理图像文件失败: {e}")
            results["error"] = str(e)
            results["success"] = False
        
        return results
    
    async def batch_process_images(self, 
                                 image_paths: List[Union[str, Path]],
                                 operations: List[str] = None,
                                 max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """批量处理图像文件
        
        Args:
            image_paths: 图像文件路径列表
            operations: 要执行的操作列表
            max_concurrent: 最大并发数
            
        Returns:
            处理结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_image(image_path):
            async with semaphore:
                return await self.process_image_file(image_path, operations)
        
        tasks = [process_single_image(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "file_path": str(image_paths[i]),
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的图像格式列表
        
        Returns:
            支持的格式列表
        """
        return self.config.supported_formats.copy()
    
    def clear_cache(self):
        """清空缓存"""
        if self.config.enable_cache and os.path.exists(self.config.cache_dir):
            try:
                import shutil
                shutil.rmtree(self.config.cache_dir)
                self._setup_cache_dir()
                logger.info("缓存已清空")
            except Exception as e:
                logger.error(f"清空缓存失败: {e}")