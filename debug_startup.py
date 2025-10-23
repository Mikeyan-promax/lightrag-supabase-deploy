#!/usr/bin/env python3
"""
Railway容器启动调试脚本
强制输出所有环境变量和配置信息，确保我们能看到真实的容器状态
"""

import os
import sys
import json
from datetime import datetime

def debug_startup():
    """调试容器启动状态"""
    
    print("=" * 80)
    print("🚀 RAILWAY容器启动调试信息")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 基本系统信息
    print("\n📋 1. 系统基本信息:")
    print("-" * 50)
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.executable}")
    
    # 2. 关键文件检查
    print("\n📁 2. 关键文件存在性检查:")
    print("-" * 50)
    critical_files = ['.env', '.env.railway', 'start.py', 'lightrag/api/config.py']
    for file_path in critical_files:
        exists = "✅ 存在" if os.path.exists(file_path) else "❌ 不存在"
        print(f"{file_path}: {exists}")
    
    # 3. Railway环境变量
    print("\n🚂 3. Railway环境变量:")
    print("-" * 50)
    railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'PORT']
    for var in railway_vars:
        value = os.environ.get(var, 'NOT_SET')
        print(f"{var}: {value}")
    
    # 4. 数据库环境变量
    print("\n🗄️ 4. 数据库环境变量:")
    print("-" * 50)
    db_vars = ['DATABASE_URL', 'PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE']
    for var in db_vars:
        value = os.environ.get(var, 'NOT_SET')
        if 'PASSWORD' in var and value != 'NOT_SET':
            print(f"{var}: {value[:10]}...{value[-10:]}")
        else:
            print(f"{var}: {value}")
    
    # 5. API密钥环境变量
    print("\n🔑 5. API密钥环境变量:")
    print("-" * 50)
    api_vars = ['DEEPSEEK_API_KEY', 'DOUBAO_API_KEY', 'OPENAI_API_KEY', 'LLM_BINDING_API_KEY']
    for var in api_vars:
        value = os.environ.get(var, 'NOT_SET')
        if value != 'NOT_SET':
            print(f"{var}: {value[:10]}...{value[-10:]} (长度: {len(value)})")
        else:
            print(f"{var}: {value}")
    
    # 6. LLM配置环境变量
    print("\n🤖 6. LLM配置环境变量:")
    print("-" * 50)
    llm_vars = ['LLM_BINDING', 'LLM_MODEL', 'LLM_BINDING_HOST', 'OPENAI_API_BASE']
    for var in llm_vars:
        value = os.environ.get(var, 'NOT_SET')
        print(f"{var}: {value}")
    
    # 7. 嵌入模型配置
    print("\n🔍 7. 嵌入模型配置:")
    print("-" * 50)
    embed_vars = ['EMBEDDING_BINDING', 'EMBEDDING_MODEL', 'EMBEDDING_BINDING_API_KEY', 'EMBEDDING_BINDING_HOST']
    for var in embed_vars:
        value = os.environ.get(var, 'NOT_SET')
        if 'KEY' in var and value != 'NOT_SET':
            print(f"{var}: {value[:10]}...{value[-10:]}")
        else:
            print(f"{var}: {value}")
    
    # 8. 检查.env文件内容
    print("\n📄 8. .env文件内容检查:")
    print("-" * 50)
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
                print(f".env文件大小: {len(content)} 字符")
                lines = content.split('\n')
                print(f".env文件行数: {len(lines)}")
                # 显示前5行（不包含敏感信息）
                for i, line in enumerate(lines[:5]):
                    if '=' in line and not any(sensitive in line.upper() for sensitive in ['KEY', 'PASSWORD', 'SECRET']):
                        print(f"  行{i+1}: {line}")
                    elif '=' in line:
                        key = line.split('=')[0]
                        print(f"  行{i+1}: {key}=***")
        except Exception as e:
            print(f"读取.env文件失败: {e}")
    else:
        print(".env文件不存在")
    
    # 9. 进程和端口信息
    print("\n🌐 9. 网络和端口信息:")
    print("-" * 50)
    port = os.environ.get('PORT', '9621')
    print(f"监听端口: {port}")
    
    # 10. 关键诊断
    print("\n🔍 10. 关键问题诊断:")
    print("-" * 50)
    
    # 检查API密钥一致性
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    llm_key = os.environ.get('LLM_BINDING_API_KEY')
    
    if deepseek_key and openai_key and llm_key:
        if deepseek_key == openai_key == llm_key:
            print("✅ API密钥配置一致")
        else:
            print("❌ API密钥配置不一致！")
            print(f"   DEEPSEEK_API_KEY: {deepseek_key[:10]}...{deepseek_key[-10:]}")
            print(f"   OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-10:]}")
            print(f"   LLM_BINDING_API_KEY: {llm_key[:10]}...{llm_key[-10:]}")
    else:
        print("❌ 关键API密钥缺失！")
        print(f"   DEEPSEEK_API_KEY: {'存在' if deepseek_key else '缺失'}")
        print(f"   OPENAI_API_KEY: {'存在' if openai_key else '缺失'}")
        print(f"   LLM_BINDING_API_KEY: {'存在' if llm_key else '缺失'}")
    
    # 检查API端点配置
    llm_host = os.environ.get('LLM_BINDING_HOST')
    openai_base = os.environ.get('OPENAI_API_BASE')
    
    if llm_host and openai_base:
        if 'deepseek' in llm_host.lower() and 'deepseek' in openai_base.lower():
            print("✅ API端点配置正确，指向DeepSeek")
        else:
            print("❌ API端点配置错误！")
            print(f"   LLM_BINDING_HOST: {llm_host}")
            print(f"   OPENAI_API_BASE: {openai_base}")
    else:
        print("❌ API端点配置缺失！")
        print(f"   LLM_BINDING_HOST: {'存在' if llm_host else '缺失'}")
        print(f"   OPENAI_API_BASE: {'存在' if openai_base else '缺失'}")
    
    print("\n" + "=" * 80)
    print("🏁 调试信息输出完成")
    print("=" * 80)
    
    # 保存调试信息到文件
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'system_info': {
            'python_version': sys.version,
            'cwd': os.getcwd(),
            'python_executable': sys.executable
        },
        'environment_variables': dict(os.environ),
        'file_existence': {file: os.path.exists(file) for file in critical_files}
    }
    
    try:
        with open('railway_debug_startup.json', 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, indent=2, ensure_ascii=False)
        print("📊 调试信息已保存到: railway_debug_startup.json")
    except Exception as e:
        print(f"❌ 保存调试信息失败: {e}")

if __name__ == '__main__':
    debug_startup()