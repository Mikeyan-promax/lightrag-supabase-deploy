"""
图像处理相关的API路由
提供图像分析、OCR、描述生成等多模态功能
"""

import asyncio
import base64
import io
import os
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    Form,
)
from pydantic import BaseModel, Field
from PIL import Image

from lightrag import LightRAG
from lightrag.utils import logger, generate_track_id
from lightrag.api.utils_api import get_combined_auth_dependency
from lightrag.multimodal import ImageProcessor, ImageProcessorConfig
from lightrag.multimodal.vision_models import VisionModelFactory
from ..config import global_args


class ImageAnalysisRequest(BaseModel):
    """图像分析请求模型"""
    
    analysis_type: Literal["ocr", "analysis", "description", "all"] = Field(
        default="all",
        description="分析类型：ocr(文字识别)、analysis(内容分析)、description(描述生成)、all(全部)"
    )
    language: str = Field(
        default="zh",
        description="语言设置，用于OCR和描述生成"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_type": "all",
                "language": "zh"
            }
        }


class ImageAnalysisResponse(BaseModel):
    """图像分析响应模型"""
    
    status: Literal["success", "error"] = Field(description="处理状态")
    message: str = Field(description="处理消息")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小(字节)")
    image_info: Dict[str, Any] = Field(description="图像基本信息")
    ocr_result: Optional[str] = Field(default=None, description="OCR识别结果")
    analysis_result: Optional[str] = Field(default=None, description="图像分析结果")
    description: Optional[str] = Field(default=None, description="图像描述")
    processing_time: float = Field(description="处理时间(秒)")
    token_usage: Optional[Dict[str, int]] = Field(default=None, description="Token使用情况")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "图像处理完成",
                "filename": "example.jpg",
                "file_size": 1024000,
                "image_info": {
                    "width": 1920,
                    "height": 1080,
                    "format": "JPEG",
                    "mode": "RGB"
                },
                "ocr_result": "识别到的文字内容",
                "analysis_result": "图像内容分析结果",
                "description": "图像描述内容",
                "processing_time": 2.5,
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                }
            }
        }


class BatchImageProcessRequest(BaseModel):
    """批量图像处理请求模型"""
    
    analysis_type: Literal["ocr", "analysis", "description", "all"] = Field(
        default="all",
        description="分析类型"
    )
    language: str = Field(default="zh", description="语言设置")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="最大并发数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_type": "all",
                "language": "zh",
                "max_concurrent": 3
            }
        }


class BatchImageProcessResponse(BaseModel):
    """批量图像处理响应模型"""
    
    status: Literal["success", "partial", "error"] = Field(description="处理状态")
    message: str = Field(description="处理消息")
    total_files: int = Field(description="总文件数")
    successful_files: int = Field(description="成功处理的文件数")
    failed_files: int = Field(description="失败的文件数")
    results: List[ImageAnalysisResponse] = Field(description="处理结果列表")
    total_processing_time: float = Field(description="总处理时间(秒)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "批量处理完成",
                "total_files": 3,
                "successful_files": 3,
                "failed_files": 0,
                "results": [],
                "total_processing_time": 7.5
            }
        }


def create_image_routes(combined_auth) -> APIRouter:
    """创建图像处理相关的API路由"""
    
    router = APIRouter(prefix="/images", tags=["图像处理"])
    
    # 支持的图像格式
    SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
    
    def is_supported_image(filename: str) -> bool:
        """检查是否为支持的图像格式"""
        return any(filename.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)
    
    def get_image_info(image: Image.Image) -> Dict[str, Any]:
        """获取图像基本信息"""
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format or "Unknown",
            "mode": image.mode,
            "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info
        }
    
    @router.post("/analyze", response_model=ImageAnalysisResponse, dependencies=[Depends(combined_auth)])
    async def analyze_image(
        file: UploadFile = File(...),
        analysis_type: str = Form(default="all"),
        language: str = Form(default="zh")
    ):
        """
        分析单个图像文件
        
        支持的分析类型：
        - ocr: 文字识别
        - analysis: 内容分析  
        - description: 描述生成
        - all: 全部分析
        """
        start_time = datetime.now()
        
        try:
            # 验证文件类型
            if not is_supported_image(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的图像格式。支持的格式: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
                )
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            # 打开图像获取基本信息
            image = Image.open(io.BytesIO(file_content))
            image_info = get_image_info(image)
            
            # 创建图像处理器配置
            config = ImageProcessorConfig(
                enable_cache=True,
                max_image_size=(2048, 2048),
                supported_formats=list(SUPPORTED_IMAGE_EXTENSIONS)
            )
            
            # 创建图像处理器
            processor = ImageProcessor(config)
            
            # 注册豆包视觉模型
            try:
                # 从环境变量获取豆包视觉模型API密钥
                doubao_api_key = os.getenv("DOUBAO_API_KEY")
                if doubao_api_key:
                    doubao_vision_model = VisionModelFactory.create_doubao_vision_model(doubao_api_key)
                    if doubao_vision_model:
                        processor.register_vision_model("default", doubao_vision_model)
                        processor.register_vision_model("doubao", doubao_vision_model)
                        logger.info("成功注册豆包视觉模型")
                    else:
                        logger.warning("豆包视觉模型创建失败，图像分析功能可能受限")
                else:
                    logger.warning("未找到豆包视觉模型API密钥，跳过豆包视觉模型注册")
            except Exception as e:
                logger.error(f"注册豆包视觉模型失败: {e}")
            
            # 执行图像处理
            ocr_result = None
            analysis_result = None
            description = None
            token_usage = None
            
            if analysis_type in ["ocr", "all"]:
                ocr_result = await processor.extract_text(file_content)
            
            if analysis_type in ["analysis", "all"]:
                analysis_result_raw = await processor.analyze_image(file_content, "请分析这张图片的内容，包括主要对象、场景、颜色等特征。")
                # 提取字符串内容
                if isinstance(analysis_result_raw, dict) and "content" in analysis_result_raw:
                    analysis_result = analysis_result_raw["content"]
                else:
                    analysis_result = str(analysis_result_raw) if analysis_result_raw else None
            
            if analysis_type in ["description", "all"]:
                description_raw = await processor.analyze_image(file_content, "请详细描述这张图片，包括主要内容、颜色、构图、风格等特征。")
                # 提取字符串内容
                if isinstance(description_raw, dict) and "content" in description_raw:
                    description = description_raw["content"]
                else:
                    description = str(description_raw) if description_raw else None
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ImageAnalysisResponse(
                status="success",
                message="图像处理完成",
                filename=file.filename,
                file_size=file_size,
                image_info=image_info,
                ocr_result=ocr_result,
                analysis_result=analysis_result,
                description=description,
                processing_time=processing_time,
                token_usage=token_usage
            )
            
        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ImageAnalysisResponse(
                status="error",
                message=f"图像处理失败: {str(e)}",
                filename=file.filename or "unknown",
                file_size=0,
                image_info={},
                processing_time=processing_time
            )
    
    @router.post("/batch-analyze", response_model=BatchImageProcessResponse, dependencies=[Depends(combined_auth)])
    async def batch_analyze_images(
        files: List[UploadFile] = File(...),
        analysis_type: str = Form(default="all"),
        language: str = Form(default="zh"),
        max_concurrent: int = Form(default=3, ge=1, le=10)
    ):
        """
        批量分析多个图像文件
        """
        start_time = datetime.now()
        
        try:
            # 过滤支持的图像文件
            valid_files = []
            for file in files:
                if is_supported_image(file.filename):
                    valid_files.append(file)
                else:
                    logger.warning(f"跳过不支持的文件格式: {file.filename}")
            
            if not valid_files:
                raise HTTPException(
                    status_code=400,
                    detail="没有找到支持的图像文件"
                )
            
            # 创建图像处理器配置
            config = ImageProcessorConfig(
                enable_cache=True,
                max_image_size=(2048, 2048),
                supported_formats=list(SUPPORTED_IMAGE_EXTENSIONS)
            )
            
            # 创建图像处理器
            processor = ImageProcessor(config)
            
            # 定义单个文件处理函数
            async def process_single_file(file: UploadFile) -> ImageAnalysisResponse:
                file_start_time = datetime.now()
                
                try:
                    # 读取文件内容
                    file_content = await file.read()
                    file_size = len(file_content)
                    
                    # 获取图像信息
                    image = Image.open(io.BytesIO(file_content))
                    image_info = get_image_info(image)
                    
                    # 执行处理
                    ocr_result = None
                    analysis_result = None
                    description = None
                    
                    if analysis_type in ["ocr", "all"]:
                        ocr_result = await processor.extract_text(file_content)
                    
                    if analysis_type in ["analysis", "all"]:
                        analysis_result_raw = await processor.analyze_image(file_content, "请分析这张图片的内容，包括主要对象、场景、颜色等特征。")
                        # 提取字符串内容
                        if isinstance(analysis_result_raw, dict) and "content" in analysis_result_raw:
                            analysis_result = analysis_result_raw["content"]
                        else:
                            analysis_result = str(analysis_result_raw) if analysis_result_raw else None
                    
                    if analysis_type in ["description", "all"]:
                        description_raw = await processor.analyze_image(file_content, "请详细描述这张图片，包括主要内容、颜色、构图、风格等特征。")
                        # 提取字符串内容
                        if isinstance(description_raw, dict) and "content" in description_raw:
                            description = description_raw["content"]
                        else:
                            description = str(description_raw) if description_raw else None
                    
                    file_processing_time = (datetime.now() - file_start_time).total_seconds()
                    
                    return ImageAnalysisResponse(
                        status="success",
                        message="处理成功",
                        filename=file.filename,
                        file_size=file_size,
                        image_info=image_info,
                        ocr_result=ocr_result,
                        analysis_result=analysis_result,
                        description=description,
                        processing_time=file_processing_time
                    )
                    
                except Exception as e:
                    file_processing_time = (datetime.now() - file_start_time).total_seconds()
                    logger.error(f"处理文件 {file.filename} 失败: {str(e)}")
                    
                    return ImageAnalysisResponse(
                        status="error",
                        message=f"处理失败: {str(e)}",
                        filename=file.filename,
                        file_size=0,
                        image_info={},
                        processing_time=file_processing_time
                    )
            
            # 使用信号量控制并发数
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(file: UploadFile) -> ImageAnalysisResponse:
                async with semaphore:
                    return await process_single_file(file)
            
            # 并发处理所有文件
            tasks = [process_with_semaphore(file) for file in valid_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            failed_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"批量处理中出现异常: {str(result)}")
                elif result.status == "error":
                    failed_count += 1
                    successful_results.append(result)
                else:
                    successful_results.append(result)
            
            total_processing_time = (datetime.now() - start_time).total_seconds()
            successful_count = len(successful_results) - failed_count
            
            # 确定整体状态
            if failed_count == 0:
                status = "success"
                message = "所有文件处理成功"
            elif successful_count == 0:
                status = "error"
                message = "所有文件处理失败"
            else:
                status = "partial"
                message = f"部分文件处理成功 ({successful_count}/{len(valid_files)})"
            
            return BatchImageProcessResponse(
                status=status,
                message=message,
                total_files=len(valid_files),
                successful_files=successful_count,
                failed_files=failed_count,
                results=successful_results,
                total_processing_time=total_processing_time
            )
            
        except Exception as e:
            logger.error(f"批量图像处理失败: {str(e)}")
            logger.error(traceback.format_exc())
            
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            return BatchImageProcessResponse(
                status="error",
                message=f"批量处理失败: {str(e)}",
                total_files=len(files),
                successful_files=0,
                failed_files=len(files),
                results=[],
                total_processing_time=total_processing_time
            )
    
    @router.get("/supported-formats")
    async def get_supported_formats():
        """获取支持的图像格式列表"""
        return {
            "supported_formats": list(SUPPORTED_IMAGE_EXTENSIONS),
            "description": "支持的图像文件格式"
        }
    
    @router.get("/vision-models")
    async def get_vision_models():
        """获取可用的视觉模型列表"""
        try:
            models = VisionModelFactory.list_models()
            return {
                "available_models": models,
                "default_model": "doubao_vision",
                "description": "可用的视觉模型"
            }
        except Exception as e:
            logger.error(f"获取视觉模型列表失败: {str(e)}")
            return {
                "available_models": ["doubao_vision"],
                "default_model": "doubao_vision",
                "description": "可用的视觉模型"
            }
    
    return router