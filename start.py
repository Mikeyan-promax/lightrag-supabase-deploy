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
    # 获取 PORT 环境变量
    port = os.environ.get('PORT', '8000')
    
    # 调试信息
    print(f"原始 PORT 环境变量: {os.environ.get('PORT', 'None')}")
    print(f"使用端口: {port}")
    
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