#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG 服务启动脚本
支持多种部署环境和配置选项
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

def setup_logging(log_level="INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('lightrag.log', encoding='utf-8')
        ]
    )

def load_environment():
    """加载环境变量配置"""
    env_files = ['.env', 'env.example']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"加载环境配置文件: {env_file}")
            # 简单的.env文件加载
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and not os.environ.get(key):
                            os.environ[key] = value
            break
    else:
        print("警告：未找到环境配置文件")

def check_dependencies():
    """检查必要的依赖"""
    try:
        import uvicorn
        import fastapi
        print("✅ 核心依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少必要依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主启动函数"""
    parser = argparse.ArgumentParser(description='LightRAG 服务启动器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=9621, help='服务器端口')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')
    parser.add_argument('--log-level', default='INFO', help='日志级别')
    parser.add_argument('--reload', action='store_true', help='开发模式自动重载')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 加载环境变量
    load_environment()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 从环境变量获取配置
    host = os.environ.get('HOST', args.host)
    port = int(os.environ.get('PORT', args.port))
    workers = int(os.environ.get('WORKERS', args.workers))
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 LightRAG Server v1.4.6                      ║
║         Fast, Lightweight RAG Server Implementation          ║
╚══════════════════════════════════════════════════════════════╝

🚀 启动配置:
    ├─ Host: {host}
    ├─ Port: {port}
    ├─ Workers: {workers}
    ├─ Log Level: {args.log_level}
    └─ Reload: {args.reload}
""")
    
    try:
        # 导入并启动应用
        from lightrag.api.app import app
        
        import uvicorn
        uvicorn.run(
            "lightrag.api.app:app",
            host=host,
            port=port,
            workers=workers if not args.reload else 1,
            log_level=args.log_level.lower(),
            reload=args.reload,
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ 无法导入应用模块: {e}")
        print("请确保LightRAG已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
