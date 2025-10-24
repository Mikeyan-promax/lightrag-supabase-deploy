#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG 服务启动脚本
支持多种部署环境和配置选项
"""

# 🔥🔥🔥 RAILWAY 强制诊断 - 版本检查 🔥🔥🔥
print("🔥" * 100)
print("🚨🚨🚨 RAILWAY 部署诊断 - 版本 v5.0 - 2025-01-24 🚨🚨🚨")
print("🔥" * 100)
print("如果你在Railway日志中看到这条消息，说明代码版本正确！")
print("🔥" * 100)

import os
import sys
import subprocess

# 🚨 集成诊断功能 - 直接在启动脚本中运行完整诊断
print("=" * 80)
print("🚨 LightRAG Railway 部署诊断开始")
print("=" * 80)

# 🔥 步骤1: 在最开始就强制设置 OPENAI_API_BASE
print("\n🔧 [步骤1] 强制设置 OPENAI_API_BASE...")
os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
print(f"✅ OPENAI_API_BASE 已设置为: {os.environ.get('OPENAI_API_BASE')}")

# 🔍 步骤2: 检查所有关键环境变量
print("\n🔍 [步骤2] 检查关键环境变量:")
env_vars = {
    'OPENAI_API_BASE': os.environ.get('OPENAI_API_BASE', 'NOT SET'),
    'OPENAI_API_KEY': 'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET',
    'LLM_BINDING': os.environ.get('LLM_BINDING', 'NOT SET'),
    'LLM_MODEL': os.environ.get('LLM_MODEL', 'NOT SET'),
    'LLM_BINDING_HOST': os.environ.get('LLM_BINDING_HOST', 'NOT SET'),
    'EMBEDDING_BINDING': os.environ.get('EMBEDDING_BINDING', 'NOT SET'),
    'EMBEDDING_MODEL': os.environ.get('EMBEDDING_MODEL', 'NOT SET'),
    'EMBEDDING_BINDING_HOST': os.environ.get('EMBEDDING_BINDING_HOST', 'NOT SET'),
}

for key, value in env_vars.items():
    status = "✅" if value != 'NOT SET' else "❌"
    print(f"  {status} {key}: {value}")

# 🔍 步骤3: 检查Railway特定环境变量
print("\n🔍 [步骤3] 检查Railway环境变量:")
railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'PORT']
for var in railway_vars:
    value = os.environ.get(var, 'NOT SET')
    status = "✅" if value != 'NOT SET' else "❌"
    print(f"  {status} {var}: {value}")

def main():
    """主启动函数"""
    # 🔥 关键修复：在最开始就强制设置OPENAI_API_BASE
    print("\n=== 🔥 强制设置API端点 ===")
    os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
    print(f"✅ 强制设置 OPENAI_API_BASE = {os.environ['OPENAI_API_BASE']}")
    
    # 检查并处理.env文件
    if os.path.exists('.env.railway') and not os.path.exists('.env'):
        print("发现.env.railway文件，复制为.env文件")
        import shutil
        shutil.copy('.env.railway', '.env')
    elif os.path.exists('.env'):
        print("使用现有的.env文件")
    else:
        print("警告：未找到.env或.env.railway文件")
    
    # 🔥 再次确认OPENAI_API_BASE设置
    current_base = os.environ.get('OPENAI_API_BASE')
    if current_base != 'https://api.deepseek.com/v1':
        print(f"⚠️  检测到OPENAI_API_BASE被覆盖为: {current_base}")
        os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
        print(f"🔧 重新强制设置 OPENAI_API_BASE = {os.environ['OPENAI_API_BASE']}")
    else:
        print(f"✅ OPENAI_API_BASE 确认正确: {current_base}")
    
    # Railway环境变量检查和设置
    print("\n=== Railway环境变量检查 ===")
    
    # 打印所有环境变量（调试用）
    print("所有环境变量:")
    for key, value in sorted(os.environ.items()):
        if 'API' in key or 'KEY' in key or 'RAILWAY' in key or 'PORT' in key:
            if 'KEY' in key:
                print(f"  {key}: {value[:20] if value else 'None'}...")
            else:
                print(f"  {key}: {value}")
    
    # 检查关键环境变量
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    doubao_key = os.environ.get('DOUBAO_API_KEY')
    
    print(f"\n检查到的API密钥:")
    print(f"  DEEPSEEK_API_KEY: {'存在' if deepseek_key else '不存在'}")
    if deepseek_key:
        print(f"    长度: {len(deepseek_key)}")
        print(f"    前缀: {deepseek_key[:10] if len(deepseek_key) >= 10 else deepseek_key}")
        print(f"    后缀: {deepseek_key[-10:] if len(deepseek_key) >= 10 else deepseek_key}")
    
    print(f"  DOUBAO_API_KEY: {'存在' if doubao_key else '不存在'}")
    
    if not deepseek_key:
        print("❌ 错误：DEEPSEEK_API_KEY 环境变量未设置")
        print("请在Railway控制台设置 DEEPSEEK_API_KEY 环境变量")
        print("当前所有环境变量:")
        for key in sorted(os.environ.keys()):
            if 'KEY' in key or 'API' in key:
                print(f"  {key}: {os.environ[key][:20] if os.environ[key] else 'None'}...")
        sys.exit(1)
    
    if not doubao_key:
        print("⚠️  警告：DOUBAO_API_KEY 环境变量未设置，使用默认值")
        os.environ['DOUBAO_API_KEY'] = '6674bc28-fc4b-47b8-8795-bf79eb01c9ff'
        doubao_key = os.environ['DOUBAO_API_KEY']
    
    # 确保API密钥格式正确
    if not deepseek_key.startswith('sk-'):
        print(f"❌ 错误：DEEPSEEK_API_KEY 格式不正确")
        print(f"  实际值: {deepseek_key}")
        print(f"  长度: {len(deepseek_key)}")
        print(f"  应该以 'sk-' 开头")
        sys.exit(1)
    
    # 设置LLM相关环境变量
    os.environ['LLM_BINDING'] = 'openai'
    os.environ['LLM_MODEL'] = 'deepseek-chat'
    os.environ['LLM_BINDING_HOST'] = 'https://api.deepseek.com'
    os.environ['LLM_BINDING_API_KEY'] = deepseek_key
    os.environ['OPENAI_API_KEY'] = deepseek_key
    
    # 关键修复：设置OPENAI_API_BASE环境变量，覆盖LightRAG源码中的默认值
    os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
    
    print(f"✅ 强制设置OPENAI_API_BASE为DeepSeek端点: https://api.deepseek.com/v1")
    
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
    print(f"DEEPSEEK_API_KEY: {deepseek_key[:10]}...{deepseek_key[-10:] if len(deepseek_key) >= 20 else deepseek_key}")
    print(f"DOUBAO_API_KEY: {doubao_key[:10]}...{doubao_key[-10:] if len(doubao_key) >= 20 else doubao_key}")
    print(f"LLM_BINDING: {os.environ.get('LLM_BINDING')}")
    print(f"LLM_MODEL: {os.environ.get('LLM_MODEL')}")
    print(f"LLM_BINDING_HOST: {os.environ.get('LLM_BINDING_HOST')}")
    print(f"LLM_BINDING_API_KEY: {os.environ.get('LLM_BINDING_API_KEY', '')[:10]}...{os.environ.get('LLM_BINDING_API_KEY', '')[-10:] if len(os.environ.get('LLM_BINDING_API_KEY', '')) >= 20 else os.environ.get('LLM_BINDING_API_KEY', '')}")
    print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', '')[:10]}...{os.environ.get('OPENAI_API_KEY', '')[-10:] if len(os.environ.get('OPENAI_API_KEY', '')) >= 20 else os.environ.get('OPENAI_API_KEY', '')}")
    
    # 验证环境变量设置是否成功
    print(f"\n=== 环境变量验证 ===")
    required_vars = [
        'LLM_BINDING', 'LLM_MODEL', 'LLM_BINDING_HOST', 'LLM_BINDING_API_KEY',
        'EMBEDDING_BINDING', 'EMBEDDING_MODEL', 'EMBEDDING_BINDING_API_KEY'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'KEY' in var:
                print(f"✅ {var}: {value[:10]}...{value[-10:] if len(value) >= 20 else value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")
    
    print(f"\n=== 最终检查 ===")
    final_deepseek = os.environ.get('LLM_BINDING_API_KEY')
    final_openai = os.environ.get('OPENAI_API_KEY')
    
    if final_deepseek == deepseek_key:
        print("✅ LLM_BINDING_API_KEY 设置正确")
    else:
        print(f"❌ LLM_BINDING_API_KEY 设置错误: {final_deepseek}")
    
    if final_openai == deepseek_key:
        print("✅ OPENAI_API_KEY 设置正确")
    else:
        print(f"❌ OPENAI_API_KEY 设置错误: {final_openai}")
    
    # 构建启动命令
    cmd = [
        sys.executable, '-m', 'lightrag.api.lightrag_server',
        '--host', '0.0.0.0',
        '--port', str(port)
    ]
    
    print(f"启动命令: {' '.join(cmd)}")
    
    # 🔥 最终检查：在启动LightRAG服务前再次确保OPENAI_API_BASE设置正确
    print(f"\n=== 🔥 最终API端点检查 ===")
    final_base = os.environ.get('OPENAI_API_BASE')
    if final_base != 'https://api.deepseek.com/v1':
        print(f"⚠️  最终检查发现OPENAI_API_BASE不正确: {final_base}")
        os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
        print(f"🔧 最终强制设置 OPENAI_API_BASE = {os.environ['OPENAI_API_BASE']}")
    else:
        print(f"✅ 最终确认OPENAI_API_BASE正确: {final_base}")
    
    # 打印所有关键环境变量的最终状态
    print(f"\n=== 🔍 最终环境变量状态 ===")
    critical_vars = {
        'OPENAI_API_BASE': os.environ.get('OPENAI_API_BASE'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', 'NOT_SET')[:20] + '...' if os.environ.get('OPENAI_API_KEY') else 'NOT_SET',
        'LLM_BINDING': os.environ.get('LLM_BINDING'),
        'LLM_MODEL': os.environ.get('LLM_MODEL'),
        'LLM_BINDING_HOST': os.environ.get('LLM_BINDING_HOST'),
        'LLM_BINDING_API_KEY': os.environ.get('LLM_BINDING_API_KEY', 'NOT_SET')[:20] + '...' if os.environ.get('LLM_BINDING_API_KEY') else 'NOT_SET'
    }
    
    for var, value in critical_vars.items():
        print(f"  {var}: {value}")
    
    print(f"\n🚀 启动LightRAG服务器...")
    print(f"📍 访问地址: http://0.0.0.0:{port}")
    
    # 启动服务
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  服务已停止")
        sys.exit(0)

# 🔍 步骤4: 加载环境变量文件
print("\n🔍 [步骤4] 加载环境变量文件...")
env_files = ['.env.railway', '.env']
for env_file in env_files:
    if os.path.exists(env_file):
        print(f"✅ 找到环境变量文件: {env_file}")
        load_dotenv(env_file, override=False)
        print(f"📁 已加载 {env_file}")
    else:
        print(f"❌ 未找到环境变量文件: {env_file}")

# 🔍 步骤5: 再次检查 OPENAI_API_BASE 是否被覆盖
print("\n🔍 [步骤5] 检查 OPENAI_API_BASE 是否被覆盖...")
current_api_base = os.environ.get('OPENAI_API_BASE')
if current_api_base != 'https://api.deepseek.com/v1':
    print(f"❌ 警告：OPENAI_API_BASE 被覆盖为: {current_api_base}")
    print("🔧 重新强制设置为 DeepSeek 端点...")
    os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
    print(f"✅ 已重新设置为: {os.environ.get('OPENAI_API_BASE')}")
else:
    print(f"✅ OPENAI_API_BASE 保持正确: {current_api_base}")

# 🔍 步骤6: 模拟 OpenAI 客户端创建测试
print("\n🔍 [步骤6] 模拟 OpenAI 客户端创建测试...")
try:
    # 模拟 LightRAG 的客户端创建逻辑
    api_key = os.environ.get('OPENAI_API_KEY')
    base_url = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    print(f"📊 客户端配置:")
    print(f"  - API Key: {'SET (' + api_key[:10] + '...)' if api_key else 'NOT SET'}")
    print(f"  - Base URL: {base_url}")
    
    if base_url == 'https://api.deepseek.com/v1':
        print("✅ API 端点配置正确 - 指向 DeepSeek")
    else:
        print(f"❌ API 端点配置错误 - 指向 {base_url}")
        
    if api_key and api_key.startswith('sk-'):
        if 'deepseek' in api_key.lower() or len(api_key) > 50:
            print("✅ API 密钥格式似乎是 DeepSeek 格式")
        else:
            print("⚠️  API 密钥可能不是 DeepSeek 格式")
    else:
        print("❌ API 密钥未设置或格式不正确")
        
except Exception as e:
    print(f"❌ 客户端测试失败: {e}")

# 🔍 步骤7: 最终状态报告
print("\n" + "=" * 80)
print("📊 最终诊断报告")
print("=" * 80)
print(f"✅ OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
print(f"✅ LLM_BINDING: {os.environ.get('LLM_BINDING', 'NOT SET')}")
print(f"✅ LLM_MODEL: {os.environ.get('LLM_MODEL', 'NOT SET')}")
print(f"✅ EMBEDDING_BINDING: {os.environ.get('EMBEDDING_BINDING', 'NOT SET')}")

if os.environ.get('OPENAI_API_BASE') == 'https://api.deepseek.com/v1':
    print("🎉 诊断结果: API 端点配置正确!")
else:
    print("❌ 诊断结果: API 端点配置仍然错误!")

print("=" * 80)
print("🚀 开始启动 LightRAG 服务...")
print("=" * 80)

if __name__ == '__main__':
    main()
