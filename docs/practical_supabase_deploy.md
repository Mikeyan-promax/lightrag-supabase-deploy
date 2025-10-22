![1758719121599](image/practical_supabase_deploy/1758719121599.png)# LightRAG Supabase 超详细部署指南（逐步操作）

## 🎯 前置准备

在开始之前，请准备：
- 一个可用的邮箱（用于注册 Supabase）
- LLM API Key（OpenAI、DeepSeek 或其他）
- Embedding API Key（推荐 OpenAI 或 Doubao）
- 部署环境（本地 Docker 或云服务器）

---

## 第一阶段：Supabase 项目创建（详细界面操作）

### 步骤 1：访问 Supabase 官网并注册

1. **打开浏览器**，访问：https://supabase.com
2. **点击页面右上角的 "Start your project" 绿色按钮**
3. **注册账户**：
   - 选择注册方式：
     - **GitHub**：点击 "Continue with GitHub"（推荐）
     - **Google**：点击 "Continue with Google"  
     - **邮箱**：点击 "Continue with email"
   - 如果选择邮箱注册：
     - 输入邮箱地址
     - 输入密码（至少8位）
     - 点击 "Sign up"
     - **检查邮箱**，点击验证链接

### 步骤 2：创建新项目

1. **登录成功后**，你会看到 Dashboard 页面
2. **点击绿色的 "New Project" 按钮**（位于页面中央或右上角）
3. **选择组织**（如果是第一次使用，会自动创建个人组织）
4. **填写项目信息**：

   **项目基本信息**：
   - **Name**：输入项目名称（例如：`lightrag-production`）
   - **Database Password**：
     - 点击🎲图标生成强密码，**或者**
     - 手动输入密码（建议至少12位，包含大小写字母、数字、特殊字符）
     - **📝 重要**：复制并保存这个密码到安全的地方！

   **地区选择**：
   - **Region**：选择离你最近的地区
     - 亚洲用户推荐：**Singapore (Southeast Asia)** 或 **Tokyo (Northeast Asia)**
     - 美洲用户推荐：**Oregon (US West)** 或 **Virginia (US East)**
     - 欧洲用户推荐：**Ireland (West Europe)**

   **定价计划**：
   - 选择 **"Free Plan"**（足够开发和小规模使用）

5. **点击绿色的 "Create new project" 按钮**
6. **等待项目初始化**（约2-3分钟，页面会显示进度条）

### 步骤 3：获取项目连接信息

项目创建完成后，你会看到项目 Dashboard：

1. **获取 API 信息**：
   - 在左侧菜单栏，点击 **"Settings"**（设置图标 ⚙️）
   - 点击 **"API"** 子菜单
   - **记录以下信息**：
     ```
     Project URL: https://xxxxxxxxxxxxx.supabase.co
     API Key (anon public): eyJ0eXAiOiJKV1QiLCJhbGciOi...
     API Key (service_role): eyJ0eXAiOiJKV1QiLCJhbGciOi...（谨慎使用）
     ```

2. **获取数据库连接信息**：

### 获取数据库连接信息

在 Supabase 项目仪表板中，点击页面顶部的 **"Connect"** 按钮。这会打开一个对话框，显示所有可用的连接选项。

你会看到以下连接方式：

#### 直接连接（Direct Connection）
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```
- 适用于持久服务器（如虚拟机、长期运行的容器）
- 支持 IPv6，如果需要 IPv4 请使用连接池

#### 会话模式连接池（Session Pooler）
```
postgres://postgres.xxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```
- 推荐用于持久连接
- 支持预处理语句
- 同时支持 IPv4 和 IPv6

#### 事务模式连接池（Transaction Pooler）
```
postgres://postgres.xxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```
- 推荐用于 serverless 环境
- 适合短暂连接
- 连接在事务结束后释放

**注意**：将连接字符串中的 `[YOUR-PASSWORD]` 替换为你在步骤2中设置的数据库密码。

---

## 第二阶段：数据库配置（SQL 操作）

### 步骤 4：启用必要的 PostgreSQL 扩展

1. **在左侧菜单中，点击 "SQL Editor"**（💻 图标）
2. **点击 "New query" 或 "+ New query" 按钮**
3. **在 SQL 编辑器中输入以下代码**：

```sql
-- 启用向量扩展（必需用于 LightRAG 的向量存储）
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 UUID 扩展（用于生成唯一标识符）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用全文搜索扩展（用于文本搜索优化）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 启用 jsonb 函数扩展（用于 JSON 数据处理）
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- 验证扩展安装成功
SELECT 
    name,
    default_version,
    installed_version 
FROM pg_available_extensions 
WHERE name IN ('vector', 'uuid-ossp', 'pg_trgm', 'btree_gin')
ORDER BY name;
```

4. **点击绿色的 "RUN" 按钮**（或按 `Ctrl/Cmd + Enter`）
5. **检查执行结果**：
   - 应该显示 "Success. No rows returned" 对于前4个命令
   - 最后一个查询应该返回4行数据，确认扩展已安装

### 步骤 5：配置数据库安全策略（可选但推荐）

1. **在 SQL Editor 中执行以下命令**：

```sql
-- 创建 LightRAG 专用 schema（可选，用于组织表结构）
CREATE SCHEMA IF NOT EXISTS lightrag;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA lightrag GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA lightrag GRANT ALL ON SEQUENCES TO postgres;
```

2. **点击 "RUN" 执行**

---

## 第三阶段：LightRAG 项目配置

### 步骤 6：获取项目代码

1. **克隆 GitHub 仓库**：
```bash
# 克隆项目到本地
git clone https://github.com/Mikeyan-promax/lightrag-supabase-deploy.git
cd lightrag-supabase-deploy
```

2. **确认项目结构**：
```bash
# 检查项目文件是否存在
ls -la
# 应该看到以下重要文件：
# - lightrag/                    # 核心代码目录
# - env.example                  # 环境变量示例文件
# - docker-compose.yml           # Docker 编排配置（包含生产环境配置）
# - Dockerfile.production        # 生产环境 Docker 镜像
# - deploy.sh                    # 自动化部署脚本
# - backup.sh                    # 数据备份脚本
# - nginx.conf                   # Nginx 反向代理配置
# - deploy_server.md             # 云服务器部署指南
```

3. **创建必要的目录（如果不存在）**：
```bash
mkdir -p inputs rag_storage logs backups
```

### 步骤 7：配置环境变量文件

项目已经提供了完整的环境变量示例文件 `env.example`，包含了所有必要的配置项：

1. **复制环境变量模板**：
```bash
# 复制环境变量模板
cp env.example .env
```

2. **编辑环境变量文件**：
```bash
# 使用你喜欢的编辑器编辑 .env 文件
nano .env
# 或者
vim .env
```

3. **必须配置的核心变量**：

**Supabase 数据库配置**：
```env
# 从 Supabase 项目设置中获取这些值
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
DATABASE_URL=postgresql://postgres:your_password@db.your-project-id.supabase.co:5432/postgres
```

**AI 模型配置**：
```env
# OpenAI 配置
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 嵌入模型配置
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
```

**服务器配置**：
```env
HOST=0.0.0.0
PORT=8000
WEBUI_TITLE='LightRAG Supabase KB'
WEBUI_DESCRIPTION="Supabase-powered Graph Based RAG System"
WORKERS=4
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**安全配置**：
```env
# 生成随机密钥: openssl rand -hex 32
SECRET_KEY=your_secret_key_here_32_characters_long
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

**存储配置（推荐使用 PostgreSQL 一体式配置）**：
```env
# PostgreSQL 存储配置 (默认推荐配置，一体式数据库)
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage

# PostgreSQL 连接配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD='your_password'
POSTGRES_DATABASE=your_database
POSTGRES_MAX_CONNECTIONS=12
```

4. **可选配置项**：

**Redis 配置**（用于缓存）：
```env
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=
REDIS_DB=0
```

**文件上传配置**：
```env
MAX_FILE_SIZE=100
ALLOWED_FILE_TYPES=.txt,.pdf,.docx,.md,.json
```

**查询优化配置**：
```env
ENABLE_LLM_CACHE=true
TOP_K=40
CHUNK_TOP_K=10
MAX_ENTITY_TOKENS=10000
MAX_RELATION_TOKENS=10000
MAX_TOTAL_TOKENS=30000
```

**并发配置**：
```env
MAX_ASYNC=4
MAX_PARALLEL_INSERT=2
EMBEDDING_FUNC_MAX_ASYNC=8
EMBEDDING_BATCH_NUM=10
```

5. **环境变量配置说明**：
   - 所有以 `#` 开头的行都是注释，可以根据需要取消注释并配置
   - `env.example` 文件包含了超过 300 行的详细配置选项
   - 大部分配置项都有默认值，只需要配置核心的数据库和 API 密钥
   - 生产环境建议启用所有安全相关配置

### 步骤 8：使用项目现有的 Docker 配置

项目已经包含了完整的 Docker 配置文件，支持开发和生产环境：

1. **查看现有的 Docker 配置**：
```bash
# 查看 docker-compose.yml（包含开发和生产环境配置）
cat docker-compose.yml

# 查看生产环境专用 Dockerfile
cat Dockerfile.production
```

2. **Docker 配置说明**：
   - **`docker-compose.yml`**：包含完整的服务编排配置
     - 开发环境服务（使用 `dev` profile）
     - 生产环境服务（默认 profile，包含 Redis、Nginx 等）
     - 资源限制、健康检查、日志配置等
   
   - **`Dockerfile.production`**：生产环境优化的镜像构建文件
     - 多阶段构建，减小镜像体积
     - 非 root 用户运行，提高安全性
     - 使用 gunicorn 作为 WSGI 服务器
     - 内置健康检查机制

3. **选择部署模式**：

   **开发环境部署**：
   ```bash
   # 启动开发环境（包含开发工具和调试功能）
   docker-compose --profile dev up --build -d
   ```

   **生产环境部署**：
   ```bash
   # 启动生产环境（优化性能和安全性）
   docker-compose up --build -d
   ```

4. **生产环境特性**：
   - Redis 缓存服务
   - Nginx 反向代理（可选）
   - 资源限制和监控
   - 自动重启策略
   - 日志轮转配置
   - 健康检查机制

---

## 第四阶段：部署前测试

### 步骤 9：测试数据库连接

1. **创建连接测试脚本**：

```bash
cat > test_connection.py << 'EOF'
import os
import psycopg2
import sys
from dotenv import load_dotenv

def test_database_connection():
    # 加载环境变量
    load_dotenv()
    
    # 获取连接参数
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT', 5432)
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    database = os.getenv('POSTGRES_DATABASE')
    ssl_mode = os.getenv('POSTGRES_SSL_MODE', 'require')
    
    print("🔍 测试数据库连接...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"SSL Mode: {ssl_mode}")
    print("-" * 50)
    
    try:
        # 尝试连接数据库
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            sslmode=ssl_mode
        )
        
        # 测试基本查询
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ 数据库连接成功!")
        print(f"PostgreSQL 版本: {version}")
        
        # 测试扩展
        cur.execute("""
            SELECT name, default_version, installed_version 
            FROM pg_available_extensions 
            WHERE name IN ('vector', 'uuid-ossp', 'pg_trgm')
            AND installed_version IS NOT NULL
            ORDER BY name;
        """)
        extensions = cur.fetchall()
        
        print(f"\n✅ 已安装的扩展:")
        for ext in extensions:
            print(f"  - {ext[0]}: {ext[2]}")
        
        # 清理
        cur.close()
        conn.close()
        print(f"\n🎉 数据库连接测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n🔧 请检查:")
        print("1. Supabase 项目是否正常运行")
        print("2. 数据库密码是否正确")
        print("3. 网络连接是否正常")
        print("4. .env 文件配置是否正确")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
EOF
```

2. **运行连接测试**：
```bash
# 安装依赖
pip install psycopg2-binary python-dotenv

# 运行测试
python test_connection.py
```

### 步骤 10：测试 API Keys

1. **创建 API 测试脚本**：

```bash
cat > test_apis.py << 'EOF'
import os
import openai
from dotenv import load_dotenv

def test_openai_api():
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
    if not api_key:
        print("❌ 未找到 OpenAI API Key")
        return False
        
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        print("✅ OpenAI API 连接成功!")
        return True
    except Exception as e:
        print(f"❌ OpenAI API 测试失败: {e}")
        return False

def test_embedding_api():
    load_dotenv()
    
    api_key = os.getenv('EMBEDDING_BINDING_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ 未找到 Embedding API Key")
        return False
        
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="This is a test"
        )
        print("✅ Embedding API 连接成功!")
        return True
    except Exception as e:
        print(f"❌ Embedding API 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 测试 API 连接...")
    print("-" * 50)
    
    llm_ok = test_openai_api()
    embedding_ok = test_embedding_api()
    
    if llm_ok and embedding_ok:
        print("\n🎉 所有 API 测试通过!")
    else:
        print("\n⚠️  部分 API 测试失败，请检查 API Keys")
EOF
```

2. **运行 API 测试**：
```bash
pip install openai
python test_apis.py
```

---

## 第五阶段：快速部署启动

### 步骤 11：使用自动化部署脚本（推荐）

项目提供了自动化部署脚本，可以一键完成大部分部署工作：

1. **使用自动化部署脚本**：
```bash
# 给脚本执行权限（Linux/macOS）
chmod +x deploy.sh

# 运行自动化部署脚本
./deploy.sh

# Windows 用户可以使用 Git Bash 或 WSL 运行，或者手动执行脚本中的命令
```

2. **脚本功能说明**：
   - 自动检查系统环境
   - 安装 Docker 和 Docker Compose（如果未安装）
   - 创建必要的目录结构
   - 配置防火墙规则
   - 启动服务并进行健康检查
   - 显示部署结果和访问信息

### 步骤 11.1：手动部署启动（备选方案）

如果不使用自动化脚本，可以手动执行以下步骤：

1. **构建和启动服务**：
```bash
# 生产环境部署（推荐）
docker-compose up --build -d

# 或者开发环境部署
docker-compose --profile dev up --build -d

# 查看服务状态
docker-compose ps
```

2. **查看启动日志**：
```bash
# 实时查看日志
docker-compose logs -f lightrag-api

# 查看最近的日志
docker-compose logs --tail=100 lightrag-api
```

3. **等待服务完全启动**（通常需要1-2分钟）

### 步骤 12：验证部署成功

1. **健康检查**：
```bash
curl http://localhost:9621/health
# 预期响应：{"status":"healthy","timestamp":"2025-XX-XX XX:XX:XX"}
```

2. **检查服务状态**：
```bash
# 检查容器状态
docker-compose ps

# 检查端口监听
netstat -tlnp | grep 9621
# 或者
lsof -i :9621
```

3. **访问 Web 界面**：
   - 打开浏览器，访问：http://localhost:9621
   - 应该看到 LightRAG 的登录界面

---

## 第六阶段：功能验证测试

### 步骤 13：登录和基本功能测试

1. **Web 界面登录**：
   - 访问：http://localhost:9621
   - 使用在 .env 文件中配置的用户名密码登录：
     - 用户名：`admin`
     - 密码：`LightRAG@2025!`

2. **API 登录测试**：
```bash
# 获取访问令牌
curl -X POST http://localhost:9621/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "LightRAG@2025!"}'

# 保存返回的 token，格式类似：
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...", "token_type": "bearer"}
```

### 步骤 14：文档上传测试

1. **创建测试文档**：
```bash
cat > ./inputs/test_document.txt << 'EOF'
# LightRAG 测试文档

这是一个测试文档，用于验证 LightRAG 系统的功能。

## 人工智能简介

人工智能（AI）是一种模拟人类智能的技术，包括：
- 机器学习
- 深度学习
- 自然语言处理
- 计算机视觉

## 知识图谱

知识图谱是一种结构化的知识表示方法，通过实体、属性和关系来描述现实世界的概念及其相互关系。

## LightRAG 特点

LightRAG 是一个基于图的检索增强生成系统，具有以下特点：
1. 快速索引构建
2. 高效的向量检索
3. 智能的知识图谱构建
4. 支持多种数据源
EOF
```

2. **通过 API 上传文档**：
```bash
# 使用之前获取的 token
TOKEN="your-access-token-here"

curl -X POST http://localhost:9621/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./inputs/test_document.txt"

# 预期响应：
# {"message": "文档上传成功", "filename": "test_document.txt", "status": "processing"}
```

### 步骤 15：查询功能测试

1. **等待文档处理完成**（通常需要几分钟）：
```bash
# 检查处理日志
docker-compose logs lightrag | grep -i "processing\|complete\|error"
```

2. **测试查询功能**：
```bash
# 测试混合查询
curl -X POST http://localhost:9621/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "什么是人工智能？",
    "mode": "hybrid",
    "stream": false
  }'

# 测试向量查询
curl -X POST http://localhost:9621/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "LightRAG 有哪些特点？",
    "mode": "vector",
    "stream": false
  }'

# 测试知识图谱查询
curl -X POST http://localhost:9621/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "知识图谱和人工智能的关系",
    "mode": "graph",
    "stream": false
  }'
```

### 步骤 16：数据库数据验证

1. **在 Supabase Dashboard 中查看数据**：
   - 登录你的 Supabase 项目
   - 点击左侧菜单的 **"Table Editor"** 
   - 你应该看到 LightRAG 创建的表：
     - `lightrag_kv_storage`
     - `lightrag_documents`  
     - `lightrag_vectors`
     - `lightrag_graph_edges`（如果使用图存储）

2. **在 SQL Editor 中验证数据**：
```sql
-- 检查文档数量
SELECT COUNT(*) as document_count FROM lightrag_documents;

-- 检查向量数据
SELECT COUNT(*) as vector_count FROM lightrag_vectors;

-- 检查键值存储
SELECT COUNT(*) as kv_count FROM lightrag_kv_storage;

-- 查看最近的文档
SELECT filename, status, created_at 
FROM lightrag_documents 
ORDER BY created_at DESC 
LIMIT 5;
```

---

## 第七阶段：生产环境优化

### 步骤 17：性能优化配置

1. **在 Supabase SQL Editor 中创建索引**：
```sql
-- 为向量查询创建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vectors_embedding_cosine 
ON lightrag_vectors USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 为文档文本搜索创建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_content_gin 
ON lightrag_documents USING gin (content gin_trgm_ops);

-- 为文档状态查询创建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_status 
ON lightrag_documents (status);

-- 为时间查询创建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at 
ON lightrag_documents (created_at DESC);
```

### 步骤 18：监控和日志配置

1. **设置日志轮转**：
```bash
cat > logrotate.conf << 'EOF'
./logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

2. **创建监控脚本**：
```bash
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "🔍 LightRAG 服务监控报告"
echo "时间: $(date)"
echo "================================"

# 检查容器状态
echo "📦 容器状态:"
docker-compose ps

# 检查内存使用
echo -e "\n💾 内存使用:"
docker stats --no-stream lightrag-supabase

# 检查磁盘使用
echo -e "\n💽 磁盘使用:"
df -h ./

# 检查服务健康
echo -e "\n🏥 服务健康检查:"
curl -s http://localhost:9621/health || echo "❌ 健康检查失败"

# 检查数据库连接
echo -e "\n🗄️ 数据库状态:"
python test_connection.py

echo -e "\n================================"
echo "监控报告完成"
EOF

chmod +x monitor.sh
```

### 步骤 19：使用项目提供的备份脚本

项目已经包含了完整的备份和恢复脚本：

1. **使用自动备份脚本**：
```bash
# 给脚本执行权限（Linux/macOS）
chmod +x backup.sh

# 运行备份脚本
./backup.sh

# Windows 用户可以使用 Git Bash 或 WSL 运行
```

2. **备份脚本功能**：
   - **应用数据备份**：RAG 存储、输入文件、日志、配置文件
   - **Docker 数据备份**：Redis 数据卷
   - **数据库备份**：Supabase PostgreSQL 数据
   - **自动清理**：删除超过 30 天的旧备份
   - **完整性验证**：验证备份文件的完整性
   - **备份报告**：生成详细的备份报告

3. **设置定期备份**：
```bash
# 添加到 crontab（每天凌晨2点备份）
echo "0 2 * * * /path/to/your/project/backup.sh" | crontab -

# 查看当前的定时任务
crontab -l
```

4. **从备份恢复**：
```bash
# 备份脚本包含恢复功能，查看帮助信息
./backup.sh --help

# 恢复特定日期的备份
./backup.sh --restore 20250101_020000
```

5. **备份文件位置**：
   - 备份文件存储在 `./backups/` 目录
   - 数据库备份：`lightrag_db_YYYYMMDD_HHMMSS.sql.gz`
   - 配置备份：`lightrag_config_YYYYMMDD_HHMMSS.tar.gz`
   - 应用数据备份：`lightrag_data_YYYYMMDD_HHMMSS.tar.gz`

---

## 第八阶段：故障排除指南

### 常见问题诊断清单

当遇到问题时，请按以下顺序检查：

1. **🔍 服务状态检查**：
```bash
docker-compose ps
docker-compose logs --tail=50 lightrag
```

2. **🌐 网络连接检查**：
```bash
# 检查 Supabase 连接
ping db.xxxxxxxxxxxxx.supabase.co
telnet db.xxxxxxxxxxxxx.supabase.co 5432
```

3. **🗄️ 数据库连接检查**：
```bash
python test_connection.py
```

4. **🔑 API 密钥检查**：
```bash
python test_apis.py
```

5. **📊 资源使用检查**：
```bash
docker stats
df -h
free -h
```

### 具体错误解决方案

#### 错误1：`could not connect to server: Connection refused`

**原因**：无法连接到 Supabase 数据库

**解决步骤**：
1. 检查 Supabase 项目状态（在 Dashboard 中确认项目运行正常）
2. 验证连接字符串中的主机名和端口
3. 检查网络防火墙设置
4. 确认 SSL 模式设置正确

#### 错误2：`password authentication failed`

**原因**：数据库密码错误

**解决步骤**：
1. 在 Supabase Dashboard → Settings → Database 中重置密码
2. 更新 `.env` 文件中的 `POSTGRES_PASSWORD`
3. 重启服务：`docker-compose restart`

#### 错误3：`extension "vector" does not exist`

**原因**：向量扩展未安装

**解决步骤**：
1. 在 Supabase SQL Editor 中执行：`CREATE EXTENSION vector;`
2. 确认扩展安装成功：`SELECT * FROM pg_extension WHERE extname = 'vector';`

#### 错误4：`API key invalid`

**原因**：LLM 或 Embedding API 密钥无效

**解决步骤**：
1. 检查 API 密钥格式和有效性
2. 确认 API 配额未超限
3. 验证 API 端点 URL 正确

#### 错误5：内存不足

**原因**：Docker 容器内存限制过低

**解决步骤**：
1. 增加 Docker 内存限制（在 docker-compose.yml 中调整）
2. 减少并发处理的文档数量
3. 优化 embedding 模型选择

---

## 🎉 部署完成验证

当你完成以上所有步骤后，你应该：

✅ **Supabase 项目运行正常**
✅ **数据库扩展已安装**
✅ **LightRAG 服务启动成功**
✅ **Web 界面可以访问**
✅ **文档上传功能正常**
✅ **查询功能返回结果**
✅ **数据存储在 Supabase 中**

### 最终测试命令

```bash
# 完整功能测试
./monitor.sh

# 或者单独验证各项功能
curl http://localhost:9621/health
python test_connection.py
python test_apis.py
```

如果所有测试都通过，恭喜你！LightRAG 已成功部署到 Supabase。

---

## 📞 获取帮助

如果在部署过程中遇到问题：

1. **查看日志**：`docker-compose logs lightrag`
2. **检查 Supabase 状态**：访问 Supabase Dashboard
3. **运行诊断脚本**：使用本指南提供的测试脚本
4. **提供错误信息**：包含具体的错误日志和环境信息

这个部署指南涵盖了从零开始到完全运行的每一个详细步骤。每个界面操作都有明确的指示，每个配置都有完整的示例。按照这个指南操作，你应该能够成功部署 LightRAG 到 Supabase。