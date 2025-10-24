#!/usr/bin/env python3
"""
Railway部署调试脚本
专门用于诊断API配置问题
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_openai_client():
    """检查OpenAI客户端配置"""
    try:
        # 模拟LightRAG中的OpenAI客户端创建过程
        from lightrag.llm.openai import create_openai_async_client
        
        print("🔍 测试OpenAI客户端创建...")
        
        # 获取当前环境变量
        api_key = os.environ.get('OPENAI_API_KEY')
        base_url = os.environ.get('OPENAI_API_BASE')
        
        print(f"  API Key: {api_key[:20] + '...' if api_key else 'NOT_SET'}")
        print(f"  Base URL: {base_url}")
        
        # 创建客户端（不实际调用API）
        client = create_openai_async_client(api_key=api_key, base_url=base_url)
        print(f"  客户端Base URL: {client.base_url}")
        
        if str(client.base_url) == 'https://api.deepseek.com/v1':
            print("✅ OpenAI客户端配置正确")
            return True
        else:
            print(f"❌ OpenAI客户端配置错误，实际使用: {client.base_url}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI客户端检查失败: {e}")
        return False

def main():
    """主调试函数"""
    
    print_section("🔍 Railway部署调试诊断")
    
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"脚本路径: {__file__}")
    
    # 🔥 第一步：强制设置OPENAI_API_BASE
    print_section("🔥 步骤1: 强制设置API端点")
    os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
    print(f"✅ 强制设置 OPENAI_API_BASE = {os.environ['OPENAI_API_BASE']}")
    
    # 第二步：加载环境变量文件
    print_section("📁 步骤2: 加载环境变量文件")
    env_files = ['.env.railway', '.env']
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"✅ 找到环境变量文件: {env_file}")
            load_dotenv(env_file, override=True)
            print(f"✅ 已加载: {env_file}")
        else:
            print(f"❌ 未找到: {env_file}")
    
    # 第三步：检查OPENAI_API_BASE是否被覆盖
    print_section("🔍 步骤3: 检查API端点是否被覆盖")
    current_base = os.environ.get('OPENAI_API_BASE')
    if current_base == 'https://api.deepseek.com/v1':
        print(f"✅ OPENAI_API_BASE 保持正确: {current_base}")
    else:
        print(f"⚠️  OPENAI_API_BASE 被覆盖为: {current_base}")
        os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
        print(f"🔧 重新强制设置: {os.environ['OPENAI_API_BASE']}")
    
    # 第四步：检查所有关键环境变量
    print_section("📋 步骤4: 检查所有关键环境变量")
    critical_vars = {
        'OPENAI_API_BASE': os.environ.get('OPENAI_API_BASE'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'DEEPSEEK_API_KEY': os.environ.get('DEEPSEEK_API_KEY'),
        'DOUBAO_API_KEY': os.environ.get('DOUBAO_API_KEY'),
        'LLM_BINDING': os.environ.get('LLM_BINDING'),
        'LLM_MODEL': os.environ.get('LLM_MODEL'),
        'LLM_BINDING_HOST': os.environ.get('LLM_BINDING_HOST'),
        'LLM_BINDING_API_KEY': os.environ.get('LLM_BINDING_API_KEY'),
        'EMBEDDING_BINDING': os.environ.get('EMBEDDING_BINDING'),
        'EMBEDDING_MODEL': os.environ.get('EMBEDDING_MODEL'),
        'EMBEDDING_BINDING_HOST': os.environ.get('EMBEDDING_BINDING_HOST'),
        'EMBEDDING_BINDING_API_KEY': os.environ.get('EMBEDDING_BINDING_API_KEY'),
    }
    
    for var, value in critical_vars.items():
        if value:
            if 'KEY' in var:
                display_value = f"{value[:10]}...{value[-10:]}" if len(value) >= 20 else value
                print(f"✅ {var}: {display_value} (长度: {len(value)})")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")
    
    # 第五步：检查Railway特定环境变量
    print_section("🚂 步骤5: 检查Railway环境变量")
    railway_vars = [
        'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_NAME', 'RAILWAY_SERVICE_NAME',
        'RAILWAY_DEPLOYMENT_ID', 'RAILWAY_REPLICA_ID', 'PORT'
    ]
    
    for var in railway_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")
    
    # 第六步：测试OpenAI客户端配置
    print_section("🧪 步骤6: 测试OpenAI客户端配置")
    client_ok = check_openai_client()
    
    # 第七步：最终诊断结果
    print_section("📊 步骤7: 最终诊断结果")
    
    issues = []
    
    # 检查API密钥
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    if not deepseek_key:
        issues.append("❌ DEEPSEEK_API_KEY 未设置")
    elif not deepseek_key.startswith('sk-'):
        issues.append(f"❌ DEEPSEEK_API_KEY 格式错误: {deepseek_key[:20]}...")
    
    # 检查API端点
    if os.environ.get('OPENAI_API_BASE') != 'https://api.deepseek.com/v1':
        issues.append(f"❌ OPENAI_API_BASE 配置错误: {os.environ.get('OPENAI_API_BASE')}")
    
    # 检查OpenAI客户端
    if not client_ok:
        issues.append("❌ OpenAI客户端配置失败")
    
    if issues:
        print("🚨 发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
        
        print("\n💡 建议解决方案:")
        print("  1. 检查Railway控制台中的DEEPSEEK_API_KEY环境变量")
        print("  2. 确保API密钥以'sk-'开头且完整")
        print("  3. 验证.env.railway文件中的OPENAI_API_BASE设置")
        print("  4. 重新部署服务以应用环境变量更改")
        
        return False
    else:
        print("✅ 所有配置检查通过！")
        print("🎉 API配置应该可以正常工作")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)