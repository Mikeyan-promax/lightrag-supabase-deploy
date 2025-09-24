# LightRAG Supabase 部署指南

## 概述

Supabase 是一个开源的 Firebase 替代方案，提供托管的 PostgreSQL 数据库、实时功能、用户认证、文件存储和边缘函数。<mcreference link="https://docs.lovable.dev/integrations/supabase" index="1">1</mcreference> 本指南将详细介绍如何将 LightRAG 部署到 Supabase 平台上。

## 为什么选择 Supabase

### 核心优势

- **完整的 PostgreSQL 数据库**：每个 Supabase 项目都是一个完整的 PostgreSQL 数据库，具有 postgres 级别的访问权限 <mcreference link="https://supabase.com/docs/guides/database/overview" index="3">3</mcreference>
- **多种连接方式**：支持直连、会话模式和事务模式的连接池 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>
- **自动生成 API**：通过 PostgREST 自动生成 RESTful API，通过 pg_graphql 生成 GraphQL API <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>
- **实时功能**：支持数据库变更的实时订阅 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>
- **扩展支持**：支持多种 PostgreSQL 扩展，包括向量数据库功能 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>

### 适用场景

- 需要托管 PostgreSQL 数据库的应用
- 需要实时数据同步的应用
- 需要快速原型开发的项目
- 需要全球分布式部署的应用

## 部署前准备

### 1. 创建 Supabase 项目

1. 访问 [Supabase 官网](https://supabase.com) 并注册账户
2. 创建新项目，选择合适的区域
3. 等待项目初始化完成（通常需要 2-3 分钟）

### 2. 获取数据库连接信息

在 Supabase 项目仪表板中：

1. 点击 **Settings** → **Database**
2. 在 **Connection string** 部分，你会看到三种连接方式：
   - **Direct connection**：直接连接到 PostgreSQL 实例 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>
   - **Session pooler**：通过代理的会话模式连接 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>
   - **Transaction pooler**：适用于无服务器环境的事务模式连接 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>

### 3. 启用必要的扩展

在 Supabase SQL 编辑器中执行以下命令：

```sql
-- 启用 pgvector 扩展（用于向量存储）
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 uuid-ossp 扩展（用于 UUID 生成）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用 pg_trgm 扩展（用于文本搜索）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## LightRAG 配置

### 环境变量配置

基于你的实际配置，创建或更新 `.env` 文件：

```bash
###########################
### 服务器配置
###########################
HOST=0.0.0.0
PORT=9621
WEBUI_TITLE='My Graph KB'
WEBUI_DESCRIPTION="Simple and Fast Graph Based RAG System"

#####################################
### 登录和 API 密钥配置
#####################################
AUTH_ACCOUNTS='admin:lightrag123'
TOKEN_SECRET=LightRAG-Secret-Key-2025
TOKEN_EXPIRE_HOURS=48
GUEST_TOKEN_EXPIRE_HOURS=24
JWT_ALGORITHM=HS256

#######################
### LLM 配置
#######################
LLM_BIND_TYPE=openai
LLM_MODEL=deepseek-chat
LLM_BINDING_HOST=https://api.deepseek.com/v1
LLM_API_KEY=your-deepseek-api-key

### OpenAI API Key（兼容性）
OPENAI_API_KEY=your-deepseek-api-key

####################################################################################
### Embedding 配置（首次处理文件后不应更改）
####################################################################################
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=doubao-embedding-text-240715
EMBEDDING_DIM=2560
EMBEDDING_BINDING_API_KEY=your-doubao-api-key
EMBEDDING_BINDING_HOST=https://ark.cn-beijing.volces.com/api/v3

### 豆包视觉模型配置（用于图像分析）
DOUBAO_API_KEY=your-doubao-api-key

############################
### 数据存储选择
############################
### PostgreSQL 存储（推荐生产环境）
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
# 注意：如果禁用知识图谱功能，不需要配置图存储
# LIGHTRAG_GRAPH_STORAGE=PGGraphStorage

### PostgreSQL 配置（Supabase）
POSTGRES_HOST=your-project-ref.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-database-password
POSTGRES_DATABASE=postgres
POSTGRES_MAX_CONNECTIONS=12

### PostgreSQL SSL 配置（Supabase 推荐）
POSTGRES_SSL_MODE=require
```

### Docker Compose 配置

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  lightrag:
    build: .
    ports:
      - "9621:9621"
    environment:
      - HOST=0.0.0.0
      - PORT=9621
    env_file:
      - .env
    volumes:
      - ./inputs:/app/inputs
      - ./rag_storage:/app/rag_storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9621/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 部署选项

### 选项 1：云服务器部署

#### 1. 准备服务器

选择支持 Docker 的云服务器（如 AWS EC2、DigitalOcean Droplet、阿里云 ECS 等）：

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 部署应用

```bash
# 克隆项目
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 Supabase 连接信息

# 启动服务
docker-compose up -d
```

### 选项 2：Railway 部署

Railway 是一个现代化的应用部署平台，支持从 GitHub 直接部署：

1. 访问 [Railway](https://railway.app) 并连接你的 GitHub 账户
2. 创建新项目，选择从 GitHub 仓库部署
3. 在环境变量中配置你的 Supabase 连接信息
4. Railway 会自动构建和部署你的应用

### 选项 3：Vercel 部署（适用于 API 模式）

如果你只需要 API 功能，可以使用 Vercel：

1. 在项目根目录创建 `vercel.json`：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "lightrag/server.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/lightrag/server.py"
    }
  ]
}
```

2. 配置环境变量并部署到 Vercel

## 部署验证

### 1. 健康检查

```bash
# 检查服务状态
curl http://your-domain:9621/health

# 预期响应
{
  "status": "healthy",
  "timestamp": "2025-01-XX XX:XX:XX"
}
```

### 2. 数据库连接测试

```bash
# 测试数据库连接
curl -X POST http://your-domain:9621/api/test-db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key"
```

### 3. API 功能测试

```bash
# 测试文档上传
curl -X POST http://your-domain:9621/api/upload \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@test.txt"

# 测试查询
curl -X POST http://your-domain:9621/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"query": "测试查询"}'
```

## 安全配置

### 1. Supabase 安全设置

在 Supabase 仪表板中：

- **Authentication** → **Settings**：配置认证策略
- **Database** → **Network Restrictions**：限制 IP 访问范围 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>
- **Settings** → **SSL enforcement**：强制 SSL 连接 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>

### 2. 应用安全配置

```bash
# 设置强 API 密钥
LIGHTRAG_API_KEY=your-very-secure-api-key-here

# 启用 SSL（生产环境）
SSL=true
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem

# 配置 CORS（如果需要）
CORS_ORIGINS=https://your-frontend-domain.com
```

## 监控和维护

### 1. 日志监控

```bash
# 查看应用日志
docker-compose logs -f lightrag

# 查看 Supabase 日志
# 在 Supabase 仪表板的 Logs 部分查看
```

### 2. 性能监控

- 使用 Supabase 仪表板监控数据库性能
- 配置 Supabase 的 Log Drains 导出日志到第三方工具 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>

### 3. 备份策略

- Supabase 提供每日自动备份 <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>
- 付费用户可以升级到时间点恢复（PITR） <mcreference link="https://supabase.com/docs/guides/getting-started/features" index="4">4</mcreference>

## 性能优化

### 1. 连接池配置

根据你的部署环境选择合适的连接模式：

- **持久化服务器**：使用直连或会话模式 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>
- **无服务器环境**：使用事务模式连接池 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>

### 2. 数据库优化

```sql
-- 为向量查询创建索引
CREATE INDEX ON your_vector_table USING ivfflat (embedding vector_cosine_ops);

-- 为文本搜索创建索引
CREATE INDEX ON your_text_table USING gin (content gin_trgm_ops);
```

## 故障排除

### 常见问题

1. **连接被拒绝**：检查 Supabase 项目状态和网络限制设置 <mcreference link="https://supabase.com/docs/guides/database/connecting-to-postgres" index="1">1</mcreference>
2. **SSL 连接失败**：确保使用正确的 SSL 模式和证书
3. **API 限制**：检查 Supabase 的使用限制和配额

### 调试命令

```bash
# 测试数据库连接
psql "postgresql://postgres:your-password@your-project-ref.supabase.co:5432/postgres?sslmode=require"

# 检查扩展状态
SELECT * FROM pg_extension;

# 查看连接状态
SELECT * FROM pg_stat_activity;
```

## 相关文档

- [LightRAG Docker 部署指南](./DockerDeployment.md)
- [LightRAG Kubernetes 部署指南](../k8s-deploy/README-zh.md)
- [Supabase 官方文档](https://supabase.com/docs)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)