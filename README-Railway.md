# LightRAG Railway 部署指南

## 📋 部署前准备

### 1. 环境变量配置
在Railway控制台中设置以下环境变量：

#### 🔑 API密钥配置
```bash
# DeepSeek LLM API密钥
LLM_API_KEY=sk-9189176321ae486c8f755145b59299eb

# 豆包Embedding API密钥  
EMBEDDING_API_KEY=6674bc28-fc4b-47b8-8795-bf79eb01c9ff
```

#### 🗄️ 数据库配置
```bash
# 阿里云RDS PostgreSQL配置
POSTGRES_HOST=pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com
POSTGRES_PORT=5432
POSTGRES_USER=lightrag_db
POSTGRES_PASSWORD=LightRAG2024!@#
POSTGRES_DATABASE=lightrag_production
```

### 2. 部署文件说明

- **Procfile**: Railway启动命令配置
- **railway.toml**: Railway部署配置
- **nixpacks.toml**: 构建配置
- **requirements.txt**: Python依赖
- **.env.railway**: Railway专用环境变量模板
- **start.py**: 智能启动脚本（自动检测环境）

## 🚀 部署步骤

### 方法1: GitHub连接部署（推荐）

1. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "添加Railway部署配置"
   git push origin master
   ```

2. **在Railway控制台**
   - 创建新项目
   - 连接GitHub仓库
   - 选择分支（master）
   - 设置环境变量

3. **等待自动部署**
   - Railway会自动检测配置文件
   - 使用Nixpacks构建
   - 启动服务

### 方法2: Railway CLI部署

1. **安装Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **登录并部署**
   ```bash
   railway login
   railway init
   railway up
   ```

## 🔧 配置说明

### 环境检测机制
启动脚本会自动检测运行环境：
- **Railway环境**: 使用`.env.railway`配置
- **本地环境**: 使用`.env`配置

### 关键配置项
- `PORT`: Railway自动分配，无需手动设置
- `HOST`: 固定为`0.0.0.0`
- API密钥通过环境变量注入
- 数据库连接使用阿里云RDS

## 🔍 部署验证

### 1. 检查部署日志
在Railway控制台查看部署日志，确认：
- ✅ 环境检测正确
- ✅ 配置加载成功
- ✅ 数据库连接正常
- ✅ 服务启动成功

### 2. 测试API端点
```bash
# 健康检查
curl https://your-app.railway.app/health

# API文档
curl https://your-app.railway.app/docs
```

## 🐛 故障排除

### 常见问题

1. **环境变量未生效**
   - 检查Railway控制台环境变量设置
   - 确认变量名称正确
   - 重新部署服务

2. **数据库连接失败**
   - 验证PostgreSQL连接信息
   - 检查网络访问权限
   - 确认数据库服务状态

3. **API密钥错误**
   - 验证DeepSeek和豆包API密钥
   - 检查API配额和权限
   - 确认服务可用性

### 调试命令
```bash
# 查看环境变量
railway run env

# 查看实时日志
railway logs

# 重新部署
railway up --detach
```

## 📊 监控和维护

### 性能监控
- Railway提供内置监控面板
- 查看CPU、内存、网络使用情况
- 监控响应时间和错误率

### 日志管理
- 实时日志查看：`railway logs -f`
- 历史日志下载
- 错误日志分析

### 扩容配置
根据使用情况调整：
- 服务实例数量
- 内存和CPU配置
- 并发连接数

## 🔐 安全建议

1. **API密钥管理**
   - 定期轮换API密钥
   - 使用Railway环境变量存储
   - 避免在代码中硬编码

2. **数据库安全**
   - 使用强密码
   - 启用SSL连接
   - 限制访问IP

3. **服务配置**
   - 启用HTTPS
   - 配置CORS策略
   - 设置访问限制

## 📞 支持

如遇到问题，请检查：
1. Railway官方文档
2. LightRAG项目文档
3. 部署日志和错误信息
4. 环境变量配置