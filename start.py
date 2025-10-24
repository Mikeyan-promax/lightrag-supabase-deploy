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
    
    # 在启动LightRAG服务前再次确保OPENAI_API_BASE设置正确
    os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com/v1'
    print(f"🔧 启动前最终确认OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
    
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
