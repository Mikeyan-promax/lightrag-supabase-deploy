# LightRAG Docker 部署指南

LightRAG 是一个轻量级的知识图谱检索增强生成系统，支持多种LLM后端和数据库存储方案。

## 🚀 安装要求

### 前提条件
- Python 3.10+
- Git
- Docker 和 Docker Compose
- 至少 4GB 内存和 2 CPU 核心（推荐 8GB 内存）

### 本地安装

1. 克隆仓库：
```bash
# Linux/MacOS
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG
```
```powershell
# Windows PowerShell
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG
```

2. 配置环境：
```bash
# Linux/MacOS
cp env.example .env
# 编辑 .env 文件配置您的首选设置
```
```powershell
# Windows PowerShell
Copy-Item env.example .env
# 编辑 .env 文件配置您的首选设置
```

3. 创建并激活虚拟环境：
```bash
# Linux/MacOS
python -m venv venv
source venv/bin/activate
```
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate
```

4. 安装依赖：
```bash
# 所有平台
pip install -r requirements.txt
```

## 🐳 Docker 部署

### 快速开始

1. 使用默认配置启动：
```bash
docker-compose up -d
```

2. 使用自定义配置启动：
```bash
# 复制并编辑环境配置文件
cp env.example .env
# 编辑 .env 文件设置您的配置
docker-compose up -d
```

### 部署架构选择

LightRAG 支持两种主要的部署架构：

#### 1. 轻量级部署（默认）
- 使用内置的 JSON 存储和 NetworkX 图存储
- 适合测试、开发和小规模使用
- 无需外部数据库

#### 2. 生产级部署
- 使用 PostgreSQL 作为统一存储后端
- 支持 KV 存储、文档状态、向量存储和图存储
- 适合生产环境和大规模使用
- 支持云端部署和水平扩展

### 配置选项

LightRAG 可以通过 `.env` 文件中的环境变量进行配置：

#### 服务器配置
- `HOST`: 服务器主机地址 (默认: 0.0.0.0)
- `PORT`: 服务器端口 (默认: 9621)
- `WEBUI_TITLE`: Web界面标题
- `LIGHTRAG_API_KEY`: API认证密钥

#### LLM 配置
- `LLM_BINDING`: LLM后端 (openai/ollama/lollms)
- `LLM_BINDING_HOST`: LLM服务器主机URL
- `LLM_MODEL`: 使用的模型名称
- `LLM_BINDING_API_KEY`: LLM API密钥

#### Embedding 配置
- `EMBEDDING_BINDING`: Embedding后端 (openai/ollama/lollms)
- `EMBEDDING_BINDING_HOST`: Embedding服务器主机URL
- `EMBEDDING_MODEL`: Embedding模型名称
- `EMBEDDING_DIM`: Embedding维度

#### PostgreSQL 数据库配置（生产级部署）
- `POSTGRES_HOST`: PostgreSQL主机地址
- `POSTGRES_PORT`: PostgreSQL端口 (默认: 5432)
- `POSTGRES_USER`: 数据库用户名
- `POSTGRES_PASSWORD`: 数据库密码
- `POSTGRES_DATABASE`: 数据库名称
- `POSTGRES_SSL_MODE`: SSL模式 (disable/require/prefer)

#### 存储配置
- `KV_STORAGE`: KV存储类型 (JsonKVStorage/PostgreSQLKVStorage)
- `VECTOR_DB_STORAGE`: 向量存储类型 (NanoVectorDBStorage/PostgreSQLVectorDBStorage)
- `GRAPH_STORAGE`: 图存储类型 (NetworkXStorage/PostgreSQLGraphStorage)
- `DOC_STATUS_STORAGE`: 文档状态存储类型 (JsonDocStatusStorage/PostgreSQLDocStatusStorage)

#### RAG 配置
- `MAX_ASYNC`: 最大异步操作数
- `MAX_TOKENS`: 最大token数量
- `CHUNK_SIZE`: 文档分块大小
- `TOP_K`: 检索的top-k结果数量

### 数据存储路径

系统使用以下路径进行数据存储：
```
data/
├── rag_storage/    # RAG数据持久化存储
└── inputs/         # 输入文档目录
```

### 部署示例

#### 1. 使用 Ollama 的轻量级部署
```env
# .env 文件配置
LLM_BINDING=ollama
LLM_BINDING_HOST=http://host.docker.internal:11434
LLM_MODEL=qwen2.5:32b
EMBEDDING_BINDING=ollama
EMBEDDING_BINDING_HOST=http://host.docker.internal:11434
EMBEDDING_MODEL=bge-m3

# 使用默认的轻量级存储
KV_STORAGE=JsonKVStorage
VECTOR_DB_STORAGE=NanoVectorDBStorage
GRAPH_STORAGE=NetworkXStorage
DOC_STATUS_STORAGE=JsonDocStatusStorage
```

> 注意：在Docker中不能直接使用localhost，需要使用host.docker.internal来访问宿主机服务。

#### 2. 使用 OpenAI 的轻量级部署
```env
# .env 文件配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=your-api-key

# 使用默认的轻量级存储
KV_STORAGE=JsonKVStorage
VECTOR_DB_STORAGE=NanoVectorDBStorage
GRAPH_STORAGE=NetworkXStorage
DOC_STATUS_STORAGE=JsonDocStatusStorage
```

#### 3. 使用 PostgreSQL 的生产级部署
```env
# .env 文件配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=your-api-key

# PostgreSQL 数据库配置
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_USER=lightrag_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DATABASE=lightrag_db
POSTGRES_SSL_MODE=require

# 使用 PostgreSQL 存储
KV_STORAGE=PostgreSQLKVStorage
VECTOR_DB_STORAGE=PostgreSQLVectorDBStorage
GRAPH_STORAGE=PostgreSQLGraphStorage
DOC_STATUS_STORAGE=PostgreSQLDocStatusStorage
```

#### 4. 云端部署配置示例（Supabase）
```env
# .env 文件配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=your-api-key

# Supabase PostgreSQL 配置
POSTGRES_HOST=db.your-project.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-supabase-password
POSTGRES_DATABASE=postgres
POSTGRES_SSL_MODE=require

# 使用 PostgreSQL 存储
KV_STORAGE=PostgreSQLKVStorage
VECTOR_DB_STORAGE=PostgreSQLVectorDBStorage
GRAPH_STORAGE=PostgreSQLGraphStorage
DOC_STATUS_STORAGE=PostgreSQLDocStatusStorage
```

### API 使用

部署完成后，您可以通过 `http://localhost:9621` 访问API

#### PowerShell 查询示例：
```powershell
$headers = @{
    "X-API-Key" = "your-api-key"
    "Content-Type" = "application/json"
}
$body = @{
    query = "您的问题"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:9621/query" -Method Post -Headers $headers -Body $body
```

#### curl 查询示例：
```bash
curl -X POST "http://localhost:9621/query" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"query": "您的问题"}'
```

#### Web 界面访问：
直接在浏览器中访问 `http://localhost:9621` 使用Web界面进行交互。

## 🌐 云端部署

### 支持的云平台

LightRAG 支持在多种云平台上部署：

- **Supabase**: 推荐的PostgreSQL云数据库服务
- **Railway**: 简单的应用部署平台
- **Vercel**: 适合前端和API部署
- **AWS/GCP/Azure**: 企业级云服务
- **DigitalOcean**: 性价比高的云服务器

### 云端部署优势

1. **自动扩展**: 根据负载自动调整资源
2. **高可用性**: 多区域部署，故障自动切换
3. **托管数据库**: 无需维护数据库基础设施
4. **SSL/TLS**: 自动HTTPS证书管理
5. **监控告警**: 内置监控和日志系统

### 部署前准备

1. **选择云服务提供商**
2. **准备PostgreSQL数据库**（推荐Supabase）
3. **配置环境变量**
4. **设置域名和SSL证书**（可选）

## 🔒 安全配置

### 生产环境安全建议：

1. **设置强API密钥**：
   ```env
   LIGHTRAG_API_KEY=your-very-secure-api-key-here
   ```

2. **启用SSL/TLS**：
   ```env
   POSTGRES_SSL_MODE=require
   ```

3. **配置防火墙规则**：
   - 仅允许必要的端口访问
   - 限制数据库访问来源

4. **使用环境变量管理敏感信息**：
   - 不要在代码中硬编码密钥
   - 使用云平台的密钥管理服务

5. **定期更新依赖**：
   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

## 📦 更新和维护

### 更新 Docker 容器：
```bash
docker-compose pull
docker-compose up -d --build
```

### 更新本地安装：
```bash
# Linux/MacOS
git pull
source venv/bin/activate
pip install -r requirements.txt
```
```powershell
# Windows PowerShell
git pull
.\venv\Scripts\Activate
pip install -r requirements.txt
```

### 数据备份

#### 轻量级部署数据备份：
```bash
# 备份 JSON 存储数据
tar -czf lightrag-backup-$(date +%Y%m%d).tar.gz data/rag_storage/
```

#### PostgreSQL 数据备份：
```bash
# 使用 pg_dump 备份数据库
pg_dump -h your-postgres-host -U lightrag_user -d lightrag_db > lightrag-backup-$(date +%Y%m%d).sql
```

### 监控和日志

#### 查看容器日志：
```bash
docker-compose logs -f lightrag
```

#### 监控系统资源：
```bash
docker stats lightrag
```

## 🚀 性能优化

### 硬件建议

- **CPU**: 至少 2 核心，推荐 4 核心以上
- **内存**: 至少 4GB，推荐 8GB 以上
- **存储**: SSD 存储，至少 20GB 可用空间
- **网络**: 稳定的互联网连接（用于LLM API调用）

### 配置优化

1. **调整并发参数**：
   ```env
   MAX_ASYNC=16
   MAX_PARALLEL_INSERT=8
   ```

2. **优化向量维度**：
   ```env
   EMBEDDING_DIM=1024  # 根据模型调整
   ```

3. **调整分块大小**：
   ```env
   CHUNK_SIZE=1200
   CHUNK_OVERLAP=100
   ```

## 🔧 故障排除

### 常见问题

1. **容器启动失败**：
   - 检查端口是否被占用
   - 验证 `.env` 文件配置
   - 查看容器日志

2. **数据库连接失败**：
   - 验证数据库连接参数
   - 检查网络连接
   - 确认数据库服务状态

3. **LLM API 调用失败**：
   - 验证 API 密钥
   - 检查网络连接
   - 确认模型名称正确

4. **内存不足**：
   - 增加系统内存
   - 调整并发参数
   - 使用更小的模型

### 调试命令

```bash
# 查看容器状态
docker-compose ps

# 进入容器调试
docker-compose exec lightrag bash

# 查看详细日志
docker-compose logs --tail=100 lightrag

# 重启服务
docker-compose restart lightrag
```

## 📚 相关文档

- [Kubernetes 部署指南](../k8s-deploy/README-zh.md)
- [Supabase 部署指南](./SupabaseDeployment.md)
- [API 文档](../lightrag/api/README.md)
- [算法说明](./Algorithm.md)

---

如需更多帮助，请访问 [GitHub Issues](https://github.com/HKUDS/LightRAG/issues) 或查看项目文档。
