#!/bin/bash
# Railway 启动脚本
# 确保 PORT 环境变量被正确解析

# 检查并处理.env文件
if [ -f ".env.railway" ] && [ ! -f ".env" ]; then
    echo "发现.env.railway文件，复制为.env文件"
    cp .env.railway .env
elif [ -f ".env" ]; then
    echo "使用现有的.env文件"
else
    echo "警告：未找到.env或.env.railway文件"
fi

echo ""
echo "=== Railway环境变量检查 ==="

# 检查关键环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ 错误：DEEPSEEK_API_KEY 环境变量未设置"
    echo "请在Railway控制台设置 DEEPSEEK_API_KEY 环境变量"
    exit 1
fi

if [ -z "$DOUBAO_API_KEY" ]; then
    echo "⚠️  警告：DOUBAO_API_KEY 环境变量未设置，使用默认值"
    export DOUBAO_API_KEY="6674bc28-fc4b-47b8-8795-bf79eb01c9ff"
fi

# 确保API密钥格式正确
if [[ ! "$DEEPSEEK_API_KEY" =~ ^sk- ]]; then
    echo "❌ 错误：DEEPSEEK_API_KEY 格式不正确: ${DEEPSEEK_API_KEY:0:20}..."
    exit 1
fi

# 设置LLM相关环境变量
export LLM_BINDING="openai"
export LLM_MODEL="deepseek-chat"
export LLM_BINDING_HOST="https://api.deepseek.com"
export LLM_BINDING_API_KEY="$DEEPSEEK_API_KEY"
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"

# 设置嵌入模型环境变量
export EMBEDDING_BINDING="openai"
export EMBEDDING_MODEL="doubao-embedding-text-240715"
export EMBEDDING_DIM="2560"
export EMBEDDING_BINDING_API_KEY="$DOUBAO_API_KEY"
export EMBEDDING_BINDING_HOST="https://ark.cn-beijing.volces.com/api/v3"

echo "✅ 环境变量设置完成"

echo ""
echo "=== 启动信息 ==="
echo "PORT: $PORT"
echo "DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:0:20}..."
echo "LLM_BINDING: $LLM_BINDING"
echo "LLM_MODEL: $LLM_MODEL"

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