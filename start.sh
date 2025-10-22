#!/bin/bash
# Railway 启动脚本
# 确保 PORT 环境变量被正确解析

# 调试信息
echo "原始 PORT 环境变量: $PORT"

# 设置默认端口（如果 PORT 未设置）
if [ -z "$PORT" ]; then
    PORT=8000
    echo "PORT 未设置，使用默认值: $PORT"
else
    echo "使用环境变量 PORT: $PORT"
fi

# 启动 LightRAG 服务器
echo "启动命令: python -m lightrag.api.lightrag_server --host 0.0.0.0 --port $PORT"
exec python -m lightrag.api.lightrag_server --host 0.0.0.0 --port "$PORT"