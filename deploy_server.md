# LightRAG Supabase 云服务器部署指南

## 概述

本指南将帮助您在云服务器上部署 LightRAG Supabase 版本。支持的云服务器包括：
- 阿里云 ECS
- 腾讯云 CVM  
- 华为云 ECS
- AWS EC2
- Google Cloud Compute Engine
- 其他支持 Docker 的 Linux 服务器

## 前置要求

### 服务器配置要求
- **最低配置**: 2核4GB内存，40GB存储
- **推荐配置**: 4核8GB内存，100GB存储
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **网络**: 公网IP，开放端口 80, 443, 8000

### 必需软件
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (可选，用于反向代理)

## 部署步骤

### 1. 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必需软件
sudo apt install -y git curl wget vim

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用 Docker 组权限
exit
```

### 2. 克隆项目

```bash
# 克隆您的 GitHub 仓库
git clone https://github.com/Mikeyan-promax/lightrag-supabase-deploy.git
cd lightrag-supabase-deploy

# 创建必要的目录
mkdir -p rag_storage inputs logs
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量
vim .env
```

**重要配置项**:
```env
# Supabase 配置
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 安全配置
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your_domain.com,your_server_ip
```

### 4. 启动服务

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 配置 Nginx 反向代理（推荐）

```bash
# 安装 Nginx
sudo apt install -y nginx

# 创建配置文件
sudo vim /etc/nginx/sites-available/lightrag
```

**Nginx 配置**:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 文件上传大小限制
        client_max_body_size 100M;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/lightrag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 配置 SSL 证书（推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your_domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 服务管理

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码并重启
git pull
docker-compose down
docker-compose up -d --build

# 查看日志
docker-compose logs -f lightrag-api

# 进入容器
docker-compose exec lightrag-api bash
```

### 监控和维护

```bash
# 查看系统资源使用
htop
df -h
docker stats

# 清理 Docker 资源
docker system prune -f
docker volume prune -f
```

## 安全配置

### 1. 防火墙设置

```bash
# 安装 UFW
sudo apt install -y ufw

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# 启用防火墙
sudo ufw enable
```

### 2. 定期备份

```bash
# 创建备份脚本
vim backup.sh
```

**备份脚本内容**:
```bash
#!/bin/bash
BACKUP_DIR="/backup/lightrag"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/lightrag_backup_$DATE.tar.gz \
    rag_storage/ \
    inputs/ \
    .env \
    docker-compose.yml

# 保留最近7天的备份
find $BACKUP_DIR -name "lightrag_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: lightrag_backup_$DATE.tar.gz"
```

```bash
# 设置执行权限
chmod +x backup.sh

# 设置定时备份
crontab -e
# 添加：每天凌晨2点备份
# 0 2 * * * /path/to/backup.sh
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep :8000
   
   # 检查 Docker 日志
   docker-compose logs lightrag-api
   ```

2. **内存不足**
   ```bash
   # 添加交换空间
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **磁盘空间不足**
   ```bash
   # 清理 Docker 镜像
   docker system prune -a
   
   # 清理日志文件
   sudo journalctl --vacuum-time=7d
   ```

### 性能优化

1. **调整 Docker 资源限制**
   ```yaml
   # 在 docker-compose.yml 中添加
   services:
     lightrag-api:
       deploy:
         resources:
           limits:
             memory: 4G
             cpus: '2.0'
   ```

2. **优化数据库连接**
   ```env
   # 在 .env 中调整
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=30
   ```

## 更新部署

```bash
# 1. 备份当前数据
./backup.sh

# 2. 拉取最新代码
git pull

# 3. 重新构建并启动
docker-compose down
docker-compose up -d --build

# 4. 验证服务状态
docker-compose ps
curl http://localhost:8000/health
```

## 监控和日志

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f lightrag-api

# 限制日志大小
# 在 docker-compose.yml 中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 健康检查

```bash
# API 健康检查
curl http://your_domain.com/health

# 数据库连接检查
curl http://your_domain.com/api/v1/health/db
```

## 支持

如果遇到问题，请：
1. 查看日志文件
2. 检查配置文件
3. 参考故障排除部分
4. 在 GitHub 仓库提交 Issue

---

**注意**: 请确保所有敏感信息（API密钥、密码等）都正确配置在 `.env` 文件中，并且该文件不会被提交到版本控制系统。