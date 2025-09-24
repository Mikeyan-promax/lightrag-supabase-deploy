# LightRAG Kubernetes 部署指南

这是用于在Kubernetes集群上部署LightRAG服务的Helm chart。

LightRAG支持多种部署架构：
1. **轻量级部署**：使用内置轻量级存储，适合测试和小规模使用
2. **PostgreSQL统一存储部署**：使用PostgreSQL作为统一存储后端，适合生产环境
3. **混合存储部署**：使用PostgreSQL和Neo4J的组合，适合大规模企业使用

> 如果您想要部署过程的视频演示，可以查看[bilibili](https://www.bilibili.com/video/BV1bUJazBEq2/)上的视频教程，对于喜欢视觉指导的用户可能会有所帮助。

## 🚀 前提条件

确保安装和配置了以下工具：

### 必需工具

* **Kubernetes集群**
  * 需要一个运行中的Kubernetes集群（版本 ≥ 1.20）
  * 对于本地开发或演示，可以使用[Minikube](https://minikube.sigs.k8s.io/docs/start/)（需要≥4个CPU，≥8GB内存）
  * 支持云端Kubernetes集群：EKS、GKE、AKS、DigitalOcean Kubernetes等

* **kubectl**
  * Kubernetes命令行工具，用于管理集群
  * 按照官方指南安装：[安装和设置kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

* **Helm**（v3.8+）
  * Kubernetes包管理器，用于安装LightRAG
  * 通过官方指南安装：[安装Helm](https://helm.sh/docs/intro/install/)

### 资源要求

| 部署类型 | CPU | 内存 | 存储 | 节点数 |
|---------|-----|------|------|--------|
| 轻量级部署 | 2 核心 | 4GB | 20GB | 1 |
| PostgreSQL部署 | 4 核心 | 8GB | 50GB | 2+ |
| 混合存储部署 | 6 核心 | 12GB | 100GB | 3+ |

## 📦 部署选项

### 选项1：轻量级部署（快速开始）

适合测试、开发和小规模使用。使用内置的JSON和NetworkX存储，无需外部数据库。

**特点：**
- 🚀 快速部署，无需配置外部数据库
- 💾 数据存储在Pod的持久卷中
- 🔧 配置简单，适合快速验证
- ⚠️ 不适合生产环境或大规模数据

**部署步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG/k8s-deploy

# 2. 设置环境变量
export OPENAI_API_BASE=<您的OPENAI_API_BASE>
export OPENAI_API_KEY=<您的OPENAI_API_KEY>

# 3. 使用便捷脚本部署
bash ./install_lightrag_lightweight.sh
```

**或者使用Helm直接部署：**

```bash
# 创建命名空间
kubectl create namespace rag

# 安装LightRAG（轻量级配置）
helm install lightrag ./lightrag-chart \
  --namespace rag \
  --set env.LLM_BINDING_API_KEY="$OPENAI_API_KEY" \
  --set env.LLM_BINDING_HOST="$OPENAI_API_BASE" \
  --set env.LIGHTRAG_KV_STORAGE="JsonKVStorage" \
  --set env.LIGHTRAG_VECTOR_STORAGE="NanoVectorDBStorage" \
  --set env.LIGHTRAG_GRAPH_STORAGE="NetworkXStorage" \
  --set env.LIGHTRAG_DOC_STATUS_STORAGE="JsonDocStatusStorage"
```

### 选项2：PostgreSQL统一存储部署（推荐生产环境）

使用PostgreSQL作为统一存储后端，支持KV存储、向量存储、图存储和文档状态存储。

**特点：**
- 🏢 适合生产环境
- 🔄 统一存储后端，简化管理
- 📈 支持水平扩展
- 🔒 企业级安全和备份

**部署步骤：**

```bash
# 1. 设置环境变量
export OPENAI_API_BASE=<您的OPENAI_API_BASE>
export OPENAI_API_KEY=<您的OPENAI_API_KEY>
export POSTGRES_PASSWORD=<您的PostgreSQL密码>

# 2. 部署PostgreSQL数据库
bash ./install_postgresql.sh

# 3. 部署LightRAG（PostgreSQL配置）
bash ./install_lightrag_postgresql.sh
```

**或者使用Helm直接部署：**

```bash
# 安装LightRAG（PostgreSQL配置）
helm install lightrag ./lightrag-chart \
  --namespace rag \
  --set env.LLM_BINDING_API_KEY="$OPENAI_API_KEY" \
  --set env.LLM_BINDING_HOST="$OPENAI_API_BASE" \
  --set env.LIGHTRAG_KV_STORAGE="PGKVStorage" \
  --set env.LIGHTRAG_VECTOR_STORAGE="PGVectorStorage" \
  --set env.LIGHTRAG_GRAPH_STORAGE="PGGraphStorage" \
  --set env.LIGHTRAG_DOC_STATUS_STORAGE="PGDocStatusStorage" \
  --set postgresql.enabled=true \
  --set postgresql.auth.postgresPassword="$POSTGRES_PASSWORD"
```

### 选项3：混合存储部署（企业级）

使用PostgreSQL和Neo4J的组合，提供最佳性能和功能。

**特点：**
- 🚀 最佳性能
- 🔍 强大的图查询能力
- 📊 专业的图数据库支持
- 🏢 适合大规模企业使用

**部署步骤：**

```bash
# 1. 设置环境变量
export OPENAI_API_BASE=<您的OPENAI_API_BASE>
export OPENAI_API_KEY=<您的OPENAI_API_KEY>
export POSTGRES_PASSWORD=<您的PostgreSQL密码>
export NEO4J_PASSWORD=<您的Neo4J密码>

# 2. 部署数据库
bash ./install_databases.sh

# 3. 部署LightRAG（混合存储配置）
bash ./install_lightrag_hybrid.sh
```

### 访问应用程序：

```bash
# 1. 在终端中运行此端口转发命令：
kubectl --namespace rag port-forward svc/lightrag 9621:9621

# 2. 当命令运行时，打开浏览器并导航到：
# http://localhost:9621
```

## 🔧 配置管理

### 环境变量配置

LightRAG支持通过环境变量进行灵活配置。以下是主要配置选项：

#### 基础服务配置
```yaml
env:
  HOST: 0.0.0.0                    # 服务监听地址
  PORT: 9621                       # 服务端口
  WEBUI_TITLE: "Graph RAG Engine"  # Web界面标题
  WEBUI_DESCRIPTION: "Simple and Fast Graph Based RAG System"  # 描述
  API_KEY: ""                      # API认证密钥（可选）
```

#### LLM配置
```yaml
env:
  LLM_BINDING: openai              # LLM服务提供商 (openai/ollama/azure)
  LLM_MODEL: gpt-4o-mini           # LLM模型名称
  LLM_BINDING_HOST: ""             # API基础URL（可选）
  LLM_BINDING_API_KEY: ""          # API密钥
  LLM_MAX_ASYNC: 16                # 最大异步操作数
  LLM_MAX_TOKENS: 32768            # 最大token数量
```

#### 嵌入模型配置
```yaml
env:
  EMBEDDING_BINDING: openai                 # 嵌入服务提供商
  EMBEDDING_MODEL: text-embedding-ada-002   # 嵌入模型
  EMBEDDING_DIM: 1536                       # 嵌入维度
  EMBEDDING_BINDING_API_KEY: ""             # API密钥
```

#### 存储配置

**轻量级存储（测试/开发）：**
```yaml
env:
  LIGHTRAG_KV_STORAGE: JsonKVStorage              # JSON键值存储
  LIGHTRAG_VECTOR_STORAGE: NanoVectorDBStorage    # 轻量级向量存储
  LIGHTRAG_GRAPH_STORAGE: NetworkXStorage         # NetworkX图存储
  LIGHTRAG_DOC_STATUS_STORAGE: JsonDocStatusStorage  # JSON文档状态存储
```

**PostgreSQL统一存储（生产环境）：**
```yaml
env:
  LIGHTRAG_KV_STORAGE: PGKVStorage              # PostgreSQL键值存储
  LIGHTRAG_VECTOR_STORAGE: PGVectorStorage      # PostgreSQL向量存储
  LIGHTRAG_GRAPH_STORAGE: PGGraphStorage        # PostgreSQL图存储
  LIGHTRAG_DOC_STATUS_STORAGE: PGDocStatusStorage  # PostgreSQL文档状态存储
  
  # PostgreSQL连接配置
  POSTGRES_HOST: postgresql                     # 数据库主机
  POSTGRES_PORT: 5432                          # 数据库端口
  POSTGRES_USER: postgres                      # 数据库用户
  POSTGRES_PASSWORD: ""                        # 数据库密码
  POSTGRES_DB: lightrag                        # 数据库名称
  POSTGRES_SSLMODE: prefer                     # SSL模式
```

**混合存储（企业级）：**
```yaml
env:
  LIGHTRAG_KV_STORAGE: PGKVStorage              # PostgreSQL键值存储
  LIGHTRAG_VECTOR_STORAGE: PGVectorStorage      # PostgreSQL向量存储
  LIGHTRAG_GRAPH_STORAGE: Neo4JStorage          # Neo4J图存储
  LIGHTRAG_DOC_STATUS_STORAGE: PGDocStatusStorage  # PostgreSQL文档状态存储
  
  # Neo4J连接配置
  NEO4J_URI: bolt://neo4j:7687                 # Neo4J连接URI
  NEO4J_USER: neo4j                            # Neo4J用户名
  NEO4J_PASSWORD: ""                           # Neo4J密码
```

### 资源配置

您可以通过修改`values.yaml`文件来配置LightRAG的资源使用：

```yaml
# 副本数量配置
replicaCount: 1  # 可根据负载需求增加

# 资源限制和请求
resources:
  limits:
    cpu: 2000m     # CPU限制（推荐：轻量级1000m，生产环境2000m+）
    memory: 4Gi    # 内存限制（推荐：轻量级2Gi，生产环境4Gi+）
  requests:
    cpu: 1000m     # CPU请求
    memory: 2Gi    # 内存请求

# 持久存储配置
persistence:
  enabled: true
  ragStorage:
    size: 20Gi     # RAG存储大小（根据数据量调整）
    storageClass: ""  # 存储类（可选）
  inputs:
    size: 10Gi     # 输入数据存储大小
    storageClass: ""  # 存储类（可选）

# 服务配置
service:
  type: ClusterIP  # 服务类型：ClusterIP/NodePort/LoadBalancer
  port: 9621       # 服务端口

# Ingress配置（可选）
ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: lightrag.local
      paths:
        - path: /
          pathType: Prefix
  tls: []
```

### 高级配置选项

#### 自动扩展配置
```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

#### 健康检查配置
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 生产环境部署（使用外部数据库）

### 1. 安装数据库
> 如果您已经准备好了数据库，可以跳过此步骤。详细信息可以在：[README.md](databases%2FREADME.md)中找到。

我们推荐使用KubeBlocks进行数据库部署。KubeBlocks是一个云原生数据库操作符，可以轻松地在Kubernetes上以生产规模运行任何数据库。

首先，安装KubeBlocks和KubeBlocks-Addons（如已安装可跳过）：
```bash
bash ./databases/01-prepare.sh
```

然后安装所需的数据库。默认情况下，这将安装PostgreSQL和Neo4J，但您可以修改[00-config.sh](databases%2F00-config.sh)以根据需要选择不同的数据库：
```bash
bash ./databases/02-install-database.sh
```

验证集群是否正在运行：
```bash
kubectl get clusters -n rag
# 预期输出：
# NAME            CLUSTER-DEFINITION   TERMINATION-POLICY   STATUS     AGE
# neo4j-cluster                        Delete               Running    39s
# pg-cluster      postgresql           Delete               Running    42s

kubectl get po -n rag
# 预期输出：
# NAME                      READY   STATUS    RESTARTS   AGE
# neo4j-cluster-neo4j-0     1/1     Running   0          58s
# pg-cluster-postgresql-0   4/4     Running   0          59s
# pg-cluster-postgresql-1   4/4     Running   0          59s
```

### 2. 安装LightRAG

LightRAG及其数据库部署在同一Kubernetes集群中，使配置变得简单。
安装脚本会自动从KubeBlocks获取所有数据库连接信息，无需手动设置数据库凭证：

```bash
export OPENAI_API_BASE=<您的OPENAI_API_BASE>
export OPENAI_API_KEY=<您的OPENAI_API_KEY>
bash ./install_lightrag.sh
```

### 访问应用程序：

```bash
# 1. 在终端中运行此端口转发命令：
kubectl --namespace rag port-forward svc/lightrag 9621:9621

# 2. 当命令运行时，打开浏览器并导航到：
# http://localhost:9621
```

## 注意事项

- 在部署前确保设置了所有必要的环境变量（API密钥和数据库密码）
- 出于安全原因，建议使用环境变量传递敏感信息，而不是直接写入脚本或values文件
- 轻量级部署适合测试和小规模使用，但数据持久性和性能可能有限
- 生产环境部署（PostgreSQL + Neo4J）推荐用于生产环境和大规模使用
- 有关更多自定义配置，请参考LightRAG官方文档
