#!/usr/bin/env python3
"""
Railway 启动脚本 - Python 版本
确保 PORT 环境变量被正确解析和处理
"""

import os
import sys
import subprocess

def main():
    """主启动函数"""
    # 检查并处理.env文件
    if os.path.exists('.env.railway') and not os.path.exists('.env'):
        print("发现.env.railway文件，复制为.env文件")
        import shutil
        shutil.copy('.env.railway', '.env')
    elif os.path.exists('.env'):
        print("使用现有的.env文件")
    else:
        print("警告：未找到.env或.env.railway文件")
    
    # Railway环境变量检查和设置
    print("\n=== Railway环境变量检查 ===")
    
    # 检查关键环境变量
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    doubao_key = os.environ.get('DOUBAO_API_KEY')
    
    if not deepseek_key:
        print("❌ 错误：DEEPSEEK_API_KEY 环境变量未设置")
        print("请在Railway控制台设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    
    if not doubao_key:
        print("⚠️  警告：DOUBAO_API_KEY 环境变量未设置，使用默认值")
        os.environ['DOUBAO_API_KEY'] = '6674bc28-fc4b-47b8-8795-bf79eb01c9ff'
    
    # 确保API密钥格式正确
    if not deepseek_key.startswith('sk-'):
        print(f"❌ 错误：DEEPSEEK_API_KEY 格式不正确: {deepseek_key[:20]}...")
        sys.exit(1)
    
    # 设置LLM相关环境变量
    os.environ['LLM_BINDING'] = 'openai'
    os.environ['LLM_MODEL'] = 'deepseek-chat'
    os.environ['LLM_BINDING_HOST'] = 'https://api.deepseek.com'
    os.environ['LLM_BINDING_API_KEY'] = deepseek_key
    os.environ['OPENAI_API_KEY'] = deepseek_key
    
    # 设置嵌入模型环境变量
    os.environ['EMBEDDING_BINDING'] = 'openai'
    os.environ['EMBEDDING_MODEL'] = 'doubao-embedding-text-240715'
    os.environ['EMBEDDING_DIM'] = '2560'
    os.environ['EMBEDDING_BINDING_API_KEY'] = os.environ.get('DOUBAO_API_KEY')
    os.environ['EMBEDDING_BINDING_HOST'] = 'https://ark.cn-beijing.volces.com/api/v3'
    
    print("✅ 环境变量设置完成")
    
    # 获取 PORT 环境变量
    port = os.environ.get('PORT', '8000')
    
    # 调试信息
    print(f"\n=== 启动信息 ===")
    print(f"PORT: {port}")
    print(f"DEEPSEEK_API_KEY: {deepseek_key[:20]}...")
    print(f"LLM_BINDING: {os.environ.get('LLM_BINDING')}")
    print(f"LLM_MODEL: {os.environ.get('LLM_MODEL')}")
    
    # 构建启动命令
    cmd = [
        sys.executable, '-m', 'lightrag.api.lightrag_server',
        '--host', '0.0.0.0',
        '--port', str(port)
    ]
    
    print(f"启动命令: {' '.join(cmd)}")
    
    # 执行命令
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("收到中断信号，正在退出...")
        sys.exit(0)

if __name__ == '__main__':
    main()