#!/bin/bash

# LightRAG Supabase 数据备份脚本
# 用于备份重要数据和配置文件

set -e

# 配置
BACKUP_DIR="/backup/lightrag"
PROJECT_DIR="$(pwd)"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lightrag_backup_$DATE"
RETENTION_DAYS=7

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 创建备份目录
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo chown $USER:$USER "$BACKUP_DIR"
        log_info "创建备份目录: $BACKUP_DIR"
    fi
}

# 备份应用数据
backup_app_data() {
    log_info "备份应用数据..."
    
    local temp_dir="/tmp/$BACKUP_NAME"
    mkdir -p "$temp_dir"
    
    # 备份RAG存储数据
    if [[ -d "rag_storage" ]]; then
        cp -r rag_storage "$temp_dir/"
        log_info "已备份 rag_storage 目录"
    fi
    
    # 备份输入文件
    if [[ -d "inputs" ]]; then
        cp -r inputs "$temp_dir/"
        log_info "已备份 inputs 目录"
    fi
    
    # 备份日志文件
    if [[ -d "logs" ]]; then
        cp -r logs "$temp_dir/"
        log_info "已备份 logs 目录"
    fi
    
    # 备份配置文件
    if [[ -f ".env" ]]; then
        cp .env "$temp_dir/"
        log_info "已备份 .env 配置文件"
    fi
    
    if [[ -f "docker-compose.yml" ]]; then
        cp docker-compose.yml "$temp_dir/"
        log_info "已备份 docker-compose.yml"
    fi
    
    if [[ -f "nginx.conf" ]]; then
        cp nginx.conf "$temp_dir/"
        log_info "已备份 nginx.conf"
    fi
    
    # 创建压缩包
    cd /tmp
    tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
    rm -rf "$temp_dir"
    
    log_success "应用数据备份完成: $BACKUP_NAME.tar.gz"
}

# 备份Docker数据
backup_docker_data() {
    log_info "备份Docker数据..."
    
    # 备份Docker volumes
    if docker volume ls | grep -q lightrag; then
        docker run --rm -v lightrag_redis_data:/data -v "$BACKUP_DIR":/backup alpine \
            tar -czf "/backup/redis_data_$DATE.tar.gz" -C /data .
        log_info "已备份Redis数据"
    fi
}

# 备份数据库（如果使用本地数据库）
backup_database() {
    log_info "检查数据库备份需求..."
    
    # 如果使用Supabase，提醒用户在Supabase控制台进行备份
    if grep -q "supabase.co" .env 2>/dev/null; then
        log_warning "检测到Supabase配置，请在Supabase控制台进行数据库备份"
        return
    fi
    
    # 如果有本地PostgreSQL配置，进行备份
    if command -v pg_dump &> /dev/null && [[ -n "$DATABASE_URL" ]]; then
        pg_dump "$DATABASE_URL" > "$BACKUP_DIR/database_$DATE.sql"
        gzip "$BACKUP_DIR/database_$DATE.sql"
        log_info "已备份本地数据库"
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份文件..."
    
    # 删除超过保留期的备份文件
    find "$BACKUP_DIR" -name "lightrag_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "redis_data_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "database_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    log_info "已清理 $RETENTION_DAYS 天前的备份文件"
}

# 生成备份报告
generate_report() {
    local report_file="$BACKUP_DIR/backup_report_$DATE.txt"
    
    cat > "$report_file" << EOF
LightRAG Supabase 备份报告
========================

备份时间: $(date)
备份名称: $BACKUP_NAME
项目目录: $PROJECT_DIR

备份内容:
- 应用数据: $BACKUP_NAME.tar.gz
- Docker数据: redis_data_$DATE.tar.gz (如果存在)
- 数据库: database_$DATE.sql.gz (如果存在)

备份大小:
$(ls -lh "$BACKUP_DIR"/*_$DATE.* 2>/dev/null || echo "无备份文件")

系统信息:
- 磁盘使用: $(df -h "$BACKUP_DIR" | tail -1)
- 内存使用: $(free -h | grep Mem)
- Docker状态: $(docker-compose ps 2>/dev/null || echo "Docker Compose未运行")

备份验证:
$(tar -tzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | head -10)
...

注意事项:
1. 请定期验证备份文件的完整性
2. 建议将备份文件同步到远程存储
3. Supabase数据库请在控制台单独备份
4. 敏感配置文件已包含在备份中，请妥善保管
EOF

    log_success "备份报告已生成: $report_file"
}

# 验证备份完整性
verify_backup() {
    log_info "验证备份完整性..."
    
    local backup_file="$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    if [[ -f "$backup_file" ]]; then
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log_success "备份文件完整性验证通过"
        else
            log_error "备份文件损坏！"
            return 1
        fi
    else
        log_error "备份文件不存在！"
        return 1
    fi
}

# 发送通知（可选）
send_notification() {
    # 如果配置了邮件或其他通知方式，可以在这里发送通知
    if [[ -n "$NOTIFICATION_EMAIL" ]]; then
        echo "LightRAG备份完成: $BACKUP_NAME" | mail -s "备份通知" "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
    
    # 如果配置了Webhook，可以发送HTTP通知
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"LightRAG备份完成: $BACKUP_NAME\"}" 2>/dev/null || true
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
LightRAG Supabase 备份脚本

用法: $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -d, --dir DIR       指定备份目录 (默认: $BACKUP_DIR)
    -r, --retention N   设置备份保留天数 (默认: $RETENTION_DAYS)
    --no-cleanup        跳过清理旧备份
    --verify-only       仅验证最新备份
    --restore FILE      从备份文件恢复

示例:
    $0                          # 执行完整备份
    $0 -d /custom/backup        # 使用自定义备份目录
    $0 -r 14                    # 保留14天的备份
    $0 --verify-only            # 仅验证备份
    $0 --restore backup.tar.gz  # 从备份恢复

环境变量:
    NOTIFICATION_EMAIL          备份完成后发送邮件通知
    NOTIFICATION_WEBHOOK        备份完成后发送Webhook通知
EOF
}

# 从备份恢复
restore_from_backup() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_warning "即将从备份恢复，这将覆盖现有数据！"
    read -p "确认继续？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "恢复操作已取消"
        exit 0
    fi
    
    log_info "停止服务..."
    docker-compose down 2>/dev/null || true
    
    log_info "从备份恢复数据..."
    tar -xzf "$backup_file" -C /tmp/
    
    local restore_dir="/tmp/$(basename "$backup_file" .tar.gz)"
    
    # 恢复数据目录
    if [[ -d "$restore_dir/rag_storage" ]]; then
        rm -rf rag_storage
        cp -r "$restore_dir/rag_storage" .
        log_info "已恢复 rag_storage"
    fi
    
    if [[ -d "$restore_dir/inputs" ]]; then
        rm -rf inputs
        cp -r "$restore_dir/inputs" .
        log_info "已恢复 inputs"
    fi
    
    # 恢复配置文件
    if [[ -f "$restore_dir/.env" ]]; then
        cp "$restore_dir/.env" .
        log_info "已恢复 .env"
    fi
    
    if [[ -f "$restore_dir/docker-compose.yml" ]]; then
        cp "$restore_dir/docker-compose.yml" .
        log_info "已恢复 docker-compose.yml"
    fi
    
    # 清理临时文件
    rm -rf "$restore_dir"
    
    log_info "重新启动服务..."
    docker-compose up -d
    
    log_success "恢复完成！"
}

# 主函数
main() {
    local skip_cleanup=false
    local verify_only=false
    local restore_file=""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --no-cleanup)
                skip_cleanup=true
                shift
                ;;
            --verify-only)
                verify_only=true
                shift
                ;;
            --restore)
                restore_file="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果是恢复操作
    if [[ -n "$restore_file" ]]; then
        restore_from_backup "$restore_file"
        exit 0
    fi
    
    # 如果只是验证
    if [[ "$verify_only" == true ]]; then
        local latest_backup=$(ls -t "$BACKUP_DIR"/lightrag_backup_*.tar.gz 2>/dev/null | head -1)
        if [[ -n "$latest_backup" ]]; then
            BACKUP_NAME=$(basename "$latest_backup" .tar.gz)
            verify_backup
        else
            log_error "未找到备份文件"
            exit 1
        fi
        exit 0
    fi
    
    # 执行完整备份
    log_info "开始LightRAG Supabase数据备份..."
    
    create_backup_dir
    backup_app_data
    backup_docker_data
    backup_database
    
    if [[ "$skip_cleanup" != true ]]; then
        cleanup_old_backups
    fi
    
    verify_backup
    generate_report
    send_notification
    
    log_success "备份完成！"
    log_info "备份文件: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
    log_info "备份大小: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi