"""
LightRAG多模态功能使用示例

展示如何使用豆包视觉模型进行图像处理和文档解析
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lightrag.multimodal import ImageProcessor, ImageProcessorConfig, MultimodalDocumentParser
from lightrag.multimodal.vision_models import setup_doubao_vision_model, VisionModelFactory

async def main():
    """主函数：演示多模态功能"""
    
    print("=== LightRAG多模态功能演示 ===\n")
    
    # 1. 设置豆包视觉模型
    print("1. 设置豆包视觉模型...")
    api_key = "6674bc28-fc4b-47b8-8795-bf79eb01c9ff"  # 从用户提供的文件中获取
    
    success = setup_doubao_vision_model(api_key)
    if not success:
        print("❌ 豆包视觉模型设置失败")
        return
    
    print("✅ 豆包视觉模型设置成功\n")
    
    # 2. 创建图像处理器
    print("2. 创建图像处理器...")
    config = ImageProcessorConfig(
        max_image_size=(1920, 1080),
        image_quality=90,
        enable_cache=True
    )
    
    image_processor = ImageProcessor(config)
    
    # 注册豆包视觉模型
    doubao_model = VisionModelFactory.create_doubao_vision_model(api_key)
    image_processor.register_vision_model("doubao", doubao_model)
    image_processor.register_vision_model("default", doubao_model)
    
    print("✅ 图像处理器创建成功\n")
    
    # 3. 创建多模态文档解析器
    print("3. 创建多模态文档解析器...")
    doc_parser = MultimodalDocumentParser(image_processor)
    print("✅ 文档解析器创建成功\n")
    
    # 4. 演示图像处理功能
    print("4. 演示图像处理功能...")
    
    # 检查是否有测试图像
    test_image_dir = project_root / "test_images"
    if test_image_dir.exists():
        image_files = list(test_image_dir.glob("*.{jpg,jpeg,png,bmp,gif}"))
        
        if image_files:
            test_image = image_files[0]
            print(f"   使用测试图像: {test_image.name}")
            
            # 处理单张图像
            result = await image_processor.process_image_file(
                test_image, 
                operations=['ocr', 'analysis', 'description']
            )
            
            if result.get("success"):
                print("   ✅ 图像处理成功")
                
                # 显示OCR结果
                ocr_result = result.get("operations", {}).get("ocr", {})
                if ocr_result.get("success"):
                    ocr_text = ocr_result.get("text", "").strip()
                    if ocr_text:
                        print(f"   📝 OCR文本: {ocr_text[:100]}...")
                    else:
                        print("   📝 OCR文本: 未检测到文字")
                
                # 显示图像分析结果
                analysis_result = result.get("operations", {}).get("analysis", {})
                if "content" in analysis_result:
                    analysis_text = analysis_result["content"]
                    print(f"   🔍 图像分析: {analysis_text[:100]}...")
                
                # 显示图像描述结果
                description_result = result.get("operations", {}).get("description", {})
                if "content" in description_result:
                    description_text = description_result["content"]
                    print(f"   📖 图像描述: {description_text[:100]}...")
                
            else:
                print(f"   ❌ 图像处理失败: {result.get('error', '未知错误')}")
        else:
            print("   ⚠️  未找到测试图像文件")
    else:
        print("   ⚠️  测试图像目录不存在")
    
    print()
    
    # 5. 演示文档解析功能
    print("5. 演示文档解析功能...")
    
    # 检查是否有测试文档
    test_docs_dir = project_root / "test_documents"
    if test_docs_dir.exists():
        doc_files = list(test_docs_dir.glob("*.{pdf,docx,pptx,xlsx}"))
        
        if doc_files:
            test_doc = doc_files[0]
            print(f"   使用测试文档: {test_doc.name}")
            
            # 解析文档
            parse_result = await doc_parser.parse_document(test_doc)
            
            if "error" not in parse_result:
                print("   ✅ 文档解析成功")
                print(f"   📄 文档类型: {parse_result.get('file_type', 'unknown')}")
                print(f"   📊 图像数量: {parse_result.get('total_images', 0)}")
                
                # 显示文本内容摘要
                text_content = parse_result.get("text_content", "").strip()
                if text_content:
                    print(f"   📝 文本内容: {text_content[:100]}...")
                
                # 如果有图像，显示处理结果
                images = parse_result.get("images", [])
                for i, img_info in enumerate(images[:3]):  # 只显示前3张图像
                    if img_info.get("processed"):
                        ocr_text = img_info.get("ocr_text", "").strip()
                        analysis = img_info.get("analysis", {}).get("content", "").strip()
                        
                        print(f"   🖼️  图像{i+1}:")
                        if ocr_text:
                            print(f"      OCR: {ocr_text[:50]}...")
                        if analysis:
                            print(f"      分析: {analysis[:50]}...")
                
            else:
                print(f"   ❌ 文档解析失败: {parse_result['error']}")
        else:
            print("   ⚠️  未找到测试文档文件")
    else:
        print("   ⚠️  测试文档目录不存在")
    
    print()
    
    # 6. 演示多模态内容提取
    print("6. 演示多模态内容提取...")
    
    if test_docs_dir.exists() and doc_files:
        test_doc = doc_files[0]
        
        # 提取多模态内容
        multimodal_content = await doc_parser.extract_multimodal_content(test_doc)
        
        if "error" not in multimodal_content:
            print("   ✅ 多模态内容提取成功")
            
            file_info = multimodal_content.get("file_info", {})
            print(f"   📄 文件: {file_info.get('path', 'unknown')}")
            print(f"   🖼️  图像数量: {file_info.get('total_images', 0)}")
            
            # 显示合并内容摘要
            combined_content = multimodal_content.get("combined_content", "").strip()
            if combined_content:
                print(f"   📋 合并内容: {combined_content[:200]}...")
            
        else:
            print(f"   ❌ 多模态内容提取失败: {multimodal_content['error']}")
    
    print()
    
    # 7. 显示缓存信息
    print("7. 缓存信息...")
    cache_dir = image_processor.config.cache_dir
    if os.path.exists(cache_dir):
        cache_files = list(Path(cache_dir).glob("*.json"))
        print(f"   📁 缓存目录: {cache_dir}")
        print(f"   📦 缓存文件数量: {len(cache_files)}")
    else:
        print("   📁 缓存目录尚未创建")
    
    print("\n=== 演示完成 ===")

def create_test_directories():
    """创建测试目录结构"""
    project_root = Path(__file__).parent.parent
    
    # 创建测试图像目录
    test_images_dir = project_root / "test_images"
    test_images_dir.mkdir(exist_ok=True)
    
    # 创建测试文档目录
    test_docs_dir = project_root / "test_documents"
    test_docs_dir.mkdir(exist_ok=True)
    
    print(f"测试目录已创建:")
    print(f"  图像目录: {test_images_dir}")
    print(f"  文档目录: {test_docs_dir}")
    print("\n请将测试文件放入相应目录中进行测试。")

if __name__ == "__main__":
    # 检查是否需要创建测试目录
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        create_test_directories()
    else:
        # 运行演示
        asyncio.run(main())