#!/bin/bash

# LightRAG Supabase 自动化部署脚本
# 适用于 Ubuntu/Debian 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_warning "此脚本主要为Ubuntu/Debian设计，其他系统可能需要手动调整"
    fi
    
    # 检查内存
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_warning "系统内存少于2GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $DISK_SPACE -lt 20 ]]; then
        log_warning "可用磁盘空间少于20GB，可能不足"
    fi
    
    log_success "系统检查完成"
}

# 安装Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker已安装，跳过安装步骤"
        return
    fi
    
    log_info "安装Docker..."
    
    # 更新包索引
    sudo apt-get update
    
    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 设置稳定版仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose已安装，跳过安装步骤"
        return
    fi
    
    log_info "安装Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 设置执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 克隆项目
clone_project() {
    local repo_url="https://github.com/Mikeyan-promax/lightrag-supabase-deploy.git"
    local project_dir="lightrag-supabase-deploy"
    
    if [[ -d "$project_dir" ]]; then
        log_info "项目目录已存在，更新代码..."
        cd "$project_dir"
        git pull
        cd ..
    else
        log_info "克隆项目..."
        git clone "$repo_url"
    fi
    
    cd "$project_dir"
    log_success "项目代码准备完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    if [[ ! -f .env ]]; then
        if [[ -f env.example ]]; then
            cp env.example .env
            log_info "已创建.env文件，请编辑配置"
        else
            log_info "创建.env文件模板..."
            cat > .env << EOF
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
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis 配置
REDIS_URL=redis://redis:6379/0
EOF
        fi
        
        log_warning "请编辑.env文件并配置必要的参数"
        log_info "使用命令: nano .env"
        read -p "配置完成后按Enter继续..."
    else
        log_info ".env文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p rag_storage
    mkdir -p inputs
    mkdir -p logs
    mkdir -p examples/input
    mkdir -p examples/output
    mkdir -p ssl
    
    log_success "目录创建完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw --force enable
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow 80
        sudo ufw allow 443
        sudo ufw allow 8000
        log_success "防火墙配置完成"
    else
        log_warning "UFW未安装，跳过防火墙配置"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 构建并启动服务
    docker-compose up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "健康检查通过"
            return 0
        fi
        
        log_info "健康检查失败，重试 ($attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done
    
    log_error "健康检查失败"
    return 1
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo
    echo "=== 部署信息 ==="
    echo "服务地址: http://$(curl -s ifconfig.me):8000"
    echo "本地地址: http://localhost:8000"
    echo "健康检查: http://localhost:8000/health"
    echo
    echo "=== 管理命令 ==="
    echo "查看服务状态: docker-compose ps"
    echo "查看日志: docker-compose logs -f"
    echo "重启服务: docker-compose restart"
    echo "停止服务: docker-compose down"
    echo "更新服务: git pull && docker-compose up -d --build"
    echo
    echo "=== 重要提醒 ==="
    echo "1. 请确保.env文件中的配置正确"
    echo "2. 建议配置域名和SSL证书"
    echo "3. 定期备份数据目录"
    echo "4. 监控服务运行状态"
}

# 主函数
main() {
    log_info "开始LightRAG Supabase部署..."
    
    check_root
    check_system
    
    # 安装依赖
    sudo apt-get update
    sudo apt-get install -y curl git wget vim htop
    
    install_docker
    install_docker_compose
    
    # 如果Docker刚安装，需要重新登录
    if ! groups | grep -q docker; then
        log_warning "Docker组权限需要重新登录生效"
        log_info "请运行: newgrp docker"
        log_info "然后重新执行此脚本"
        exit 0
    fi
    
    clone_project
    setup_environment
    create_directories
    setup_firewall
    start_services
    
    if health_check; then
        show_deployment_info
    else
        log_error "部署失败，请检查配置和日志"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi