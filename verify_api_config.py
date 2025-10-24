#!/usr/bin/env python3
"""
API配置验证脚本
在启动服务前验证所有API配置是否正确
"""

import os
import sys
import asyncio
from pathlib import Path

def print_header():
    """打印标题"""
    print("\n" + "="*80)
    print("🔧 LightRAG API配置验证脚本")
    print("="*80)

def check_environment_variables():
    """检查关键环境变量"""
    print("\n📋 检查环境变量:")
    
    required_vars = {
        'OPENAI_API_KEY': '用于DeepSeek API认证',
        'LLM_BINDING': 'LLM绑定类型',
        'LLM_MODEL': 'LLM模型名称',
        'EMBEDDING_BINDING': '嵌入模型绑定类型',
        'EMBEDDING_MODEL': '嵌入模型名称'
    }
    
    optional_vars = {
        'OPENAI_API_BASE': 'API端点地址',
        'LLM_BINDING_HOST': 'LLM服务主机',
        'EMBEDDING_BINDING_HOST': '嵌入服务主机'
    }
    
    all_good = True
    
    # 检查必需变量
    for var, desc in required_vars.items():
        value = os.environ.get(var)
        if value:
            if var == 'OPENAI_API_KEY':
                print(f"  ✅ {var}: {value[:20]}... ({desc})")
            else:
                print(f"  ✅ {var}: {value} ({desc})")
        else:
            print(f"  ❌ {var}: 未设置 ({desc})")
            all_good = False
    
    # 检查可选变量
    for var, desc in optional_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"  ℹ️  {var}: {value} ({desc})")
        else:
            print(f"  ⚠️  {var}: 未设置 ({desc})")
    
    return all_good

def test_openai_client():
    """测试OpenAI客户端配置"""
    print("\n🔍 测试OpenAI客户端配置:")
    
    try:
        # 导入LightRAG的OpenAI模块
        from lightrag.llm.openai import create_openai_async_client
        
        # 获取API密钥
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("  ❌ 无法测试：OPENAI_API_KEY未设置")
            return False
        
        # 创建客户端
        client = create_openai_async_client(api_key=api_key)
        
        print(f"  📡 客户端Base URL: {client.base_url}")
        print(f"  🔑 API Key前缀: {api_key[:20]}...")
        
        # 检查端点是否正确
        if str(client.base_url) == "https://api.deepseek.com/v1":
            print("  ✅ API端点配置正确 - 使用DeepSeek")
            return True
        elif str(client.base_url) == "https://api.openai.com/v1":
            print("  ❌ API端点配置错误 - 仍在使用OpenAI")
            return False
        else:
            print(f"  ⚠️  API端点未知: {client.base_url}")
            return False
            
    except Exception as e:
        print(f"  ❌ 客户端测试失败: {e}")
        return False

async def test_api_connection():
    """测试API连接"""
    print("\n🌐 测试API连接:")
    
    try:
        from lightrag.llm.openai import create_openai_async_client
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("  ❌ 跳过连接测试：API密钥未设置")
            return False
        
        client = create_openai_async_client(api_key=api_key)
        
        # 尝试简单的API调用
        print("  🔄 发送测试请求...")
        
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("  ✅ API连接成功")
        print(f"  📝 响应: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"  ❌ API连接失败: {e}")
        return False

def main():
    """主验证函数"""
    print_header()
    
    # 检查环境变量
    env_ok = check_environment_variables()
    
    # 测试客户端配置
    client_ok = test_openai_client()
    
    # 测试API连接
    try:
        connection_ok = asyncio.run(test_api_connection())
    except Exception as e:
        print(f"  ❌ 连接测试异常: {e}")
        connection_ok = False
    
    # 总结
    print("\n" + "="*80)
    print("📊 验证结果总结:")
    print(f"  环境变量: {'✅ 通过' if env_ok else '❌ 失败'}")
    print(f"  客户端配置: {'✅ 通过' if client_ok else '❌ 失败'}")
    print(f"  API连接: {'✅ 通过' if connection_ok else '❌ 失败'}")
    
    if env_ok and client_ok and connection_ok:
        print("\n🎉 所有验证通过！可以启动服务")
        return True
    else:
        print("\n⚠️  验证失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)